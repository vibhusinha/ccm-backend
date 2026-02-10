import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.club import Club
from app.models.club_member import ClubMember
from app.models.pending_club_registration import PendingClubRegistration
from app.models.profile import Profile
from app.models.registration_request import RegistrationRequest


class RegistrationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_approved_clubs(self) -> list[dict]:
        member_count_subq = (
            select(func.count())
            .select_from(ClubMember)
            .where(ClubMember.club_id == Club.id)
            .correlate(Club)
            .scalar_subquery()
        )
        stmt = (
            select(Club, member_count_subq.label("member_count"))
            .where(Club.status == "active")
            .order_by(Club.name)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": club.id,
                "name": club.name,
                "slug": club.slug,
                "logo_url": club.logo_url,
                "primary_color": club.primary_color,
                "member_count": count or 0,
            }
            for club, count in rows
        ]

    async def get_my_status(self, user_id: uuid.UUID) -> dict:
        # Check if already a member of any club
        member_stmt = select(ClubMember).where(ClubMember.user_id == user_id)
        member_result = await self.db.execute(member_stmt)
        member = member_result.scalar_one_or_none()
        if member:
            club = await self.db.get(Club, member.club_id)
            return {
                "status": "approved",
                "club_id": member.club_id,
                "club_name": club.name if club else None,
                "rejection_reason": None,
            }

        # Check for pending/rejected registration request
        stmt = (
            select(RegistrationRequest)
            .where(RegistrationRequest.user_id == user_id)
            .order_by(RegistrationRequest.requested_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        request = result.scalar_one_or_none()
        if request:
            club = await self.db.get(Club, request.club_id)
            return {
                "status": request.status,
                "club_id": request.club_id,
                "club_name": club.name if club else None,
                "rejection_reason": request.rejection_reason,
            }

        # Check for pending club registration
        club_stmt = (
            select(PendingClubRegistration)
            .where(PendingClubRegistration.requested_by == user_id)
            .order_by(PendingClubRegistration.requested_at.desc())
            .limit(1)
        )
        club_result = await self.db.execute(club_stmt)
        pending_club = club_result.scalar_one_or_none()
        if pending_club:
            return {
                "status": f"club_{pending_club.status}",
                "club_id": None,
                "club_name": pending_club.club_name,
                "rejection_reason": pending_club.rejection_reason,
            }

        return {
            "status": "none",
            "club_id": None,
            "club_name": None,
            "rejection_reason": None,
        }

    async def get_pending_for_club(self, club_id: uuid.UUID) -> list[dict]:
        stmt = (
            select(RegistrationRequest, Profile.email, Profile.full_name)
            .join(Profile, RegistrationRequest.user_id == Profile.id)
            .where(
                RegistrationRequest.club_id == club_id,
                RegistrationRequest.status == "pending",
            )
            .order_by(RegistrationRequest.requested_at.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": req.id,
                "user_id": req.user_id,
                "club_id": req.club_id,
                "status": req.status,
                "requested_at": req.requested_at,
                "reviewed_at": req.reviewed_at,
                "rejection_reason": req.rejection_reason,
                "user_email": email,
                "user_full_name": full_name,
            }
            for req, email, full_name in rows
        ]

    async def get_all_pending(self) -> list[dict]:
        stmt = (
            select(RegistrationRequest, Profile.email, Profile.full_name)
            .join(Profile, RegistrationRequest.user_id == Profile.id)
            .where(RegistrationRequest.status == "pending")
            .order_by(RegistrationRequest.requested_at.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": req.id,
                "user_id": req.user_id,
                "club_id": req.club_id,
                "status": req.status,
                "requested_at": req.requested_at,
                "reviewed_at": req.reviewed_at,
                "rejection_reason": req.rejection_reason,
                "user_email": email,
                "user_full_name": full_name,
            }
            for req, email, full_name in rows
        ]

    async def get_pending_clubs(self) -> list[PendingClubRegistration]:
        stmt = (
            select(PendingClubRegistration)
            .where(PendingClubRegistration.status == "pending")
            .order_by(PendingClubRegistration.requested_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_clubs_with_users(self) -> list[dict]:
        stmt = (
            select(PendingClubRegistration, Profile.email, Profile.full_name)
            .join(Profile, PendingClubRegistration.requested_by == Profile.id)
            .where(PendingClubRegistration.status == "pending")
            .order_by(PendingClubRegistration.requested_at.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": pcr.id,
                "requested_by": pcr.requested_by,
                "club_name": pcr.club_name,
                "club_slug": pcr.club_slug,
                "status": pcr.status,
                "requested_at": pcr.requested_at,
                "reviewed_at": pcr.reviewed_at,
                "rejection_reason": pcr.rejection_reason,
                "requester_email": email,
                "requester_full_name": full_name,
            }
            for pcr, email, full_name in rows
        ]

    async def update_requested_club(
        self, user_id: uuid.UUID, club_id: uuid.UUID
    ) -> RegistrationRequest:
        club = await self.db.get(Club, club_id)
        if not club or club.status != "active":
            raise NotFoundError("Club not found or not active")

        stmt = select(RegistrationRequest).where(
            RegistrationRequest.user_id == user_id,
            RegistrationRequest.status == "pending",
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.club_id = club_id
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        req = RegistrationRequest(
            user_id=user_id, club_id=club_id, status="pending"
        )
        self.db.add(req)
        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def approve_registration(
        self,
        registration_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        role: str = "player",
    ) -> ClubMember:
        stmt = select(RegistrationRequest).where(
            RegistrationRequest.id == registration_id
        )
        result = await self.db.execute(stmt)
        req = result.scalar_one_or_none()
        if not req:
            raise NotFoundError("Registration request not found")
        if req.status != "pending":
            raise ConflictError(f"Request is already {req.status}")

        member = ClubMember(user_id=req.user_id, club_id=req.club_id, role=role)
        self.db.add(member)

        req.status = "approved"
        req.reviewed_at = datetime.now(timezone.utc)
        req.reviewed_by = reviewer_id

        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def reject_registration(
        self,
        registration_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        reason: str | None = None,
    ) -> RegistrationRequest:
        stmt = select(RegistrationRequest).where(
            RegistrationRequest.id == registration_id
        )
        result = await self.db.execute(stmt)
        req = result.scalar_one_or_none()
        if not req:
            raise NotFoundError("Registration request not found")
        if req.status != "pending":
            raise ConflictError(f"Request is already {req.status}")

        req.status = "rejected"
        req.reviewed_at = datetime.now(timezone.utc)
        req.reviewed_by = reviewer_id
        req.rejection_reason = reason

        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def submit_club(
        self, user_id: uuid.UUID, club_name: str
    ) -> PendingClubRegistration:
        slug = re.sub(r"[^a-z0-9]+", "-", club_name.lower()).strip("-")

        existing_club = await self.db.execute(
            select(Club).where(Club.slug == slug)
        )
        if existing_club.scalar_one_or_none():
            raise ConflictError("A club with this name already exists")

        existing_pending = await self.db.execute(
            select(PendingClubRegistration).where(
                PendingClubRegistration.club_slug == slug,
                PendingClubRegistration.status == "pending",
            )
        )
        if existing_pending.scalar_one_or_none():
            raise ConflictError("A club with this name is already pending approval")

        pcr = PendingClubRegistration(
            requested_by=user_id,
            club_name=club_name,
            club_slug=slug,
            status="pending",
        )
        self.db.add(pcr)
        await self.db.flush()
        await self.db.refresh(pcr)
        return pcr

    async def approve_club(
        self, pending_club_id: uuid.UUID, reviewer_id: uuid.UUID
    ) -> dict:
        stmt = select(PendingClubRegistration).where(
            PendingClubRegistration.id == pending_club_id
        )
        result = await self.db.execute(stmt)
        pcr = result.scalar_one_or_none()
        if not pcr:
            raise NotFoundError("Pending club registration not found")
        if pcr.status != "pending":
            raise ConflictError(f"Registration is already {pcr.status}")

        club = Club(name=pcr.club_name, slug=pcr.club_slug)
        self.db.add(club)
        await self.db.flush()

        member = ClubMember(
            user_id=pcr.requested_by, club_id=club.id, role="clubadmin"
        )
        self.db.add(member)

        pcr.status = "approved"
        pcr.reviewed_at = datetime.now(timezone.utc)
        pcr.reviewed_by = reviewer_id

        await self.db.flush()
        await self.db.refresh(club)

        return {
            "club_id": str(club.id),
            "club_name": club.name,
            "club_slug": club.slug,
        }

    async def reject_club(
        self,
        pending_club_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        reason: str | None = None,
    ) -> PendingClubRegistration:
        stmt = select(PendingClubRegistration).where(
            PendingClubRegistration.id == pending_club_id
        )
        result = await self.db.execute(stmt)
        pcr = result.scalar_one_or_none()
        if not pcr:
            raise NotFoundError("Pending club registration not found")
        if pcr.status != "pending":
            raise ConflictError(f"Registration is already {pcr.status}")

        pcr.status = "rejected"
        pcr.reviewed_at = datetime.now(timezone.utc)
        pcr.reviewed_by = reviewer_id
        pcr.rejection_reason = reason

        await self.db.flush()
        await self.db.refresh(pcr)
        return pcr
