import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.club import Club
from app.models.club_member import ClubMember
from app.models.platform_admin import PlatformAdmin
from app.models.platform_setting import PlatformSetting
from app.models.profile import Profile


class PlatformService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_setup_status(self) -> dict:
        result = await self.db.execute(
            select(func.count()).select_from(PlatformAdmin).where(PlatformAdmin.is_active.is_(True))
        )
        admin_count = result.scalar_one()
        has_admin = admin_count > 0
        return {
            "needed": not has_admin,
            "has_admin": has_admin,
            "is_complete": has_admin,
        }

    async def bootstrap(self, user_id: uuid.UUID, platform_name: str) -> PlatformAdmin:
        # Check if already bootstrapped
        status = await self.get_setup_status()
        if status["has_admin"]:
            raise ValueError("Platform already has an admin")

        # Create platform admin
        admin = PlatformAdmin(user_id=user_id, is_active=True)
        self.db.add(admin)

        # Set platform name
        result = await self.db.execute(
            select(PlatformSetting).where(PlatformSetting.key == "platform_name")
        )
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = platform_name
            setting.updated_at = datetime.now(timezone.utc)
        else:
            self.db.add(PlatformSetting(key="platform_name", value=platform_name))

        await self.db.flush()

        # Log the action
        await self.log_action(
            admin_id=user_id,
            action="platform_bootstrap",
            target_type="platform",
            target_id=None,
            details={"platform_name": platform_name},
        )

        await self.db.flush()
        await self.db.refresh(admin)
        return admin

    async def get_settings(self) -> dict:
        result = await self.db.execute(select(PlatformSetting))
        settings = result.scalars().all()
        return {s.key: s.value for s in settings}

    async def get_all_clubs(self) -> list[dict]:
        member_count_subq = (
            select(func.count())
            .select_from(ClubMember)
            .where(ClubMember.club_id == Club.id)
            .correlate(Club)
            .scalar_subquery()
        )

        stmt = select(
            Club,
            member_count_subq.label("member_count"),
        ).order_by(Club.created_at.desc())

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": club.id,
                "name": club.name,
                "slug": club.slug,
                "status": club.status,
                "member_count": count or 0,
                "created_at": club.created_at,
                "suspended_at": club.suspended_at,
                "suspension_reason": club.suspension_reason,
            }
            for club, count in rows
        ]

    async def get_club(self, club_id: uuid.UUID) -> dict | None:
        member_count_subq = (
            select(func.count())
            .select_from(ClubMember)
            .where(ClubMember.club_id == Club.id)
            .correlate(Club)
            .scalar_subquery()
        )

        stmt = select(
            Club,
            member_count_subq.label("member_count"),
        ).where(Club.id == club_id)

        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if not row:
            return None

        club, count = row
        return {
            "id": club.id,
            "name": club.name,
            "slug": club.slug,
            "status": club.status,
            "member_count": count or 0,
            "created_at": club.created_at,
            "suspended_at": club.suspended_at,
            "suspension_reason": club.suspension_reason,
        }

    async def suspend_club(
        self, club_id: uuid.UUID, reason: str, admin_id: uuid.UUID
    ) -> dict | None:
        result = await self.db.execute(select(Club).where(Club.id == club_id))
        club = result.scalar_one_or_none()
        if not club:
            return None

        club.status = "suspended"
        club.suspended_at = datetime.now(timezone.utc)
        club.suspension_reason = reason
        await self.db.flush()

        await self.log_action(
            admin_id=admin_id,
            action="club_suspended",
            target_type="club",
            target_id=club_id,
            details={"reason": reason, "club_name": club.name},
        )

        return {"id": club.id, "status": club.status}

    async def reactivate_club(self, club_id: uuid.UUID, admin_id: uuid.UUID) -> dict | None:
        result = await self.db.execute(select(Club).where(Club.id == club_id))
        club = result.scalar_one_or_none()
        if not club:
            return None

        club.status = "active"
        club.suspended_at = None
        club.suspension_reason = None
        await self.db.flush()

        await self.log_action(
            admin_id=admin_id,
            action="club_reactivated",
            target_type="club",
            target_id=club_id,
            details={"club_name": club.name},
        )

        return {"id": club.id, "status": club.status}

    async def delete_club(
        self, club_id: uuid.UUID, reason: str, admin_id: uuid.UUID
    ) -> dict | None:
        result = await self.db.execute(select(Club).where(Club.id == club_id))
        club = result.scalar_one_or_none()
        if not club:
            return None

        club.status = "deleted"
        club.suspension_reason = reason
        await self.db.flush()

        await self.log_action(
            admin_id=admin_id,
            action="club_deleted",
            target_type="club",
            target_id=club_id,
            details={"reason": reason, "club_name": club.name},
        )

        return {"id": club.id, "status": club.status}

    async def get_admins(self) -> list[dict]:
        stmt = (
            select(PlatformAdmin, Profile)
            .join(Profile, PlatformAdmin.user_id == Profile.id)
            .where(PlatformAdmin.is_active.is_(True))
            .order_by(PlatformAdmin.created_at)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": admin.id,
                "user_id": admin.user_id,
                "email": profile.email,
                "full_name": profile.full_name,
                "is_active": admin.is_active,
                "permissions_list": ["manage_clubs", "view_analytics"],
                "created_at": admin.created_at,
                "last_login_at": None,
            }
            for admin, profile in rows
        ]

    async def add_admin(self, user_id: uuid.UUID, acting_admin_id: uuid.UUID) -> PlatformAdmin:
        # Check if already an admin
        result = await self.db.execute(
            select(PlatformAdmin).where(PlatformAdmin.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.is_active:
                raise ValueError("User is already a platform admin")
            existing.is_active = True
            await self.db.flush()
            await self.db.refresh(existing)
            admin = existing
        else:
            admin = PlatformAdmin(user_id=user_id, is_active=True)
            self.db.add(admin)
            await self.db.flush()
            await self.db.refresh(admin)

        await self.log_action(
            admin_id=acting_admin_id,
            action="admin_added",
            target_type="platform_admin",
            target_id=user_id,
            details={},
        )

        return admin

    async def remove_admin(self, admin_id: uuid.UUID, acting_admin_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(PlatformAdmin).where(PlatformAdmin.id == admin_id)
        )
        admin = result.scalar_one_or_none()
        if not admin:
            return False

        admin.is_active = False
        await self.db.flush()

        await self.log_action(
            admin_id=acting_admin_id,
            action="admin_removed",
            target_type="platform_admin",
            target_id=admin.user_id,
            details={},
        )

        return True

    async def get_audit_log(self, limit: int = 50) -> list[dict]:
        stmt = (
            select(AuditLog, Profile.email)
            .outerjoin(Profile, AuditLog.admin_id == Profile.id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": entry.id,
                "admin_id": entry.admin_id,
                "admin_email": email or "Unknown",
                "action": entry.action,
                "target_type": entry.target_type,
                "target_id": entry.target_id,
                "details": entry.details or {},
                "created_at": entry.created_at,
            }
            for entry, email in rows
        ]

    async def log_action(
        self,
        admin_id: uuid.UUID | None,
        action: str,
        target_type: str,
        target_id: uuid.UUID | None = None,
        details: dict | None = None,
    ) -> None:
        entry = AuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
        )
        self.db.add(entry)
        await self.db.flush()
