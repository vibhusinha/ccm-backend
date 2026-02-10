from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.club_member import ClubMember
from app.models.role import Role
from app.models.role_permission import RolePermission


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active(self) -> list[Role]:
        stmt = (
            select(Role)
            .where(Role.is_active.is_(True))
            .order_by(Role.hierarchy_level)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, role_id: UUID) -> Role | None:
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_permissions(self) -> list[Role]:
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.hierarchy_level)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_permissions(self, user_id: UUID, club_id: UUID) -> dict:
        stmt = select(ClubMember).where(
            ClubMember.user_id == user_id,
            ClubMember.club_id == club_id,
        )
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("User is not a member of this club")

        role_stmt = (
            select(Role)
            .where(Role.name == member.role)
            .options(selectinload(Role.permissions))
        )
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalar_one_or_none()

        permission_keys: list[str] = []
        if role:
            permission_keys = [rp.permission_key for rp in role.permissions if rp.granted]

        return {
            "user_id": user_id,
            "club_id": club_id,
            "role": member.role,
            "permissions": permission_keys,
        }

    async def create_role(
        self,
        name: str,
        display_name: str,
        description: str | None,
        hierarchy_level: int,
        permission_keys: list[str],
    ) -> Role:
        existing = await self.db.execute(select(Role).where(Role.name == name))
        if existing.scalar_one_or_none():
            raise ConflictError(f"Role '{name}' already exists")

        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            hierarchy_level=hierarchy_level,
            is_system_role=False,
            is_active=True,
        )
        self.db.add(role)
        await self.db.flush()

        for key in permission_keys:
            perm = RolePermission(role_id=role.id, permission_key=key, granted=True)
            self.db.add(perm)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def update_role(
        self,
        role_id: UUID,
        display_name: str | None,
        description: str | None,
        hierarchy_level: int | None,
        is_active: bool | None,
        permission_keys: list[str] | None,
    ) -> Role:
        role = await self.get_by_id(role_id)
        if not role:
            raise NotFoundError("Role not found")
        if role.is_system_role:
            raise ConflictError("Cannot modify a system role")

        if display_name is not None:
            role.display_name = display_name
        if description is not None:
            role.description = description
        if hierarchy_level is not None:
            role.hierarchy_level = hierarchy_level
        if is_active is not None:
            role.is_active = is_active

        if permission_keys is not None:
            await self.db.execute(
                delete(RolePermission).where(RolePermission.role_id == role_id)
            )
            for key in permission_keys:
                perm = RolePermission(role_id=role_id, permission_key=key, granted=True)
                self.db.add(perm)

        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def delete_role(self, role_id: UUID) -> bool:
        role = await self.get_by_id(role_id)
        if not role:
            return False
        if role.is_system_role:
            raise ConflictError("Cannot delete a system role")
        await self.db.delete(role)
        await self.db.flush()
        return True

    async def has_single_admin(self, club_id: UUID) -> dict:
        stmt = (
            select(func.count())
            .select_from(ClubMember)
            .where(
                ClubMember.club_id == club_id,
                ClubMember.role.in_(["clubadmin", "secretary", "treasurer"]),
            )
        )
        result = await self.db.execute(stmt)
        count = result.scalar_one()
        return {"has_single_admin": count <= 1, "admin_count": count}
