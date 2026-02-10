from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchandise_category import MerchandiseCategory
from app.models.merchandise_item import MerchandiseItem
from app.models.merchandise_order import MerchandiseOrder
from app.models.merchandise_order_item import MerchandiseOrderItem
from app.models.merchandise_variant import MerchandiseVariant
from app.models.profile import Profile
from app.services.base import BaseService


class MerchCategoryService(BaseService[MerchandiseCategory]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=MerchandiseCategory, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> list[MerchandiseCategory]:
        stmt = self._scoped_query().order_by(MerchandiseCategory.display_order.asc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class MerchItemService(BaseService[MerchandiseItem]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=MerchandiseItem, db=db, club_id=club_id)

    async def get_all_with_category(self) -> list[dict]:
        stmt = (
            select(MerchandiseItem, MerchandiseCategory.name.label("category_name"))
            .outerjoin(MerchandiseCategory, MerchandiseItem.category_id == MerchandiseCategory.id)
            .where(MerchandiseItem.club_id == self.club_id)
            .order_by(MerchandiseItem.name)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                **{c.key: getattr(item, c.key) for c in MerchandiseItem.__table__.columns},
                "category_name": cat_name,
            }
            for item, cat_name in rows
        ]

    async def get_low_stock(self) -> list[MerchandiseItem]:
        stmt = (
            self._scoped_query()
            .where(
                MerchandiseItem.is_active.is_(True),
                MerchandiseItem.stock_quantity <= MerchandiseItem.low_stock_threshold,
            )
            .order_by(MerchandiseItem.stock_quantity.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_summary(self) -> dict:
        total = await self.db.execute(
            select(func.count()).where(MerchandiseItem.club_id == self.club_id)
        )
        active = await self.db.execute(
            select(func.count()).where(
                MerchandiseItem.club_id == self.club_id,
                MerchandiseItem.is_active.is_(True),
            )
        )
        categories = await self.db.execute(
            select(func.count()).where(MerchandiseCategory.club_id == self.club_id)
        )
        low_stock = await self.db.execute(
            select(func.count()).where(
                MerchandiseItem.club_id == self.club_id,
                MerchandiseItem.is_active.is_(True),
                MerchandiseItem.stock_quantity <= MerchandiseItem.low_stock_threshold,
            )
        )
        orders = await self.db.execute(
            select(func.count()).where(MerchandiseOrder.club_id == self.club_id)
        )
        pending = await self.db.execute(
            select(func.count()).where(
                MerchandiseOrder.club_id == self.club_id,
                MerchandiseOrder.status == "pending",
            )
        )
        return {
            "total_items": total.scalar_one(),
            "active_items": active.scalar_one(),
            "total_categories": categories.scalar_one(),
            "low_stock_count": low_stock.scalar_one(),
            "total_orders": orders.scalar_one(),
            "pending_orders": pending.scalar_one(),
        }


class MerchVariantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_item(self, item_id: UUID) -> list[MerchandiseVariant]:
        stmt = (
            select(MerchandiseVariant)
            .where(MerchandiseVariant.item_id == item_id)
            .order_by(MerchandiseVariant.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, item_id: UUID, **kwargs) -> MerchandiseVariant:
        variant = MerchandiseVariant(item_id=item_id, **kwargs)
        self.db.add(variant)
        await self.db.flush()
        await self.db.refresh(variant)
        return variant

    async def update(self, variant_id: UUID, **kwargs) -> MerchandiseVariant | None:
        stmt = select(MerchandiseVariant).where(MerchandiseVariant.id == variant_id)
        result = await self.db.execute(stmt)
        variant = result.scalar_one_or_none()
        if not variant:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(variant, key, value)
        await self.db.flush()
        await self.db.refresh(variant)
        return variant

    async def delete(self, variant_id: UUID) -> bool:
        stmt = select(MerchandiseVariant).where(MerchandiseVariant.id == variant_id)
        result = await self.db.execute(stmt)
        variant = result.scalar_one_or_none()
        if not variant:
            return False
        await self.db.delete(variant)
        await self.db.flush()
        return True


class MerchOrderService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    async def get_all(self) -> list[dict]:
        stmt = (
            select(MerchandiseOrder, Profile.display_name.label("user_name"))
            .outerjoin(Profile, MerchandiseOrder.user_id == Profile.id)
            .where(MerchandiseOrder.club_id == self.club_id)
            .order_by(MerchandiseOrder.created_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        orders = []
        for order, user_name in rows:
            items = await self._get_order_items(order.id)
            orders.append({
                "id": order.id,
                "club_id": order.club_id,
                "user_id": order.user_id,
                "status": order.status,
                "total_amount": order.total_amount,
                "notes": order.notes,
                "created_at": order.created_at,
                "items": items,
                "user_name": user_name,
            })
        return orders

    async def get_by_id(self, order_id: UUID) -> dict | None:
        stmt = (
            select(MerchandiseOrder, Profile.display_name.label("user_name"))
            .outerjoin(Profile, MerchandiseOrder.user_id == Profile.id)
            .where(MerchandiseOrder.id == order_id)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if not row:
            return None
        order, user_name = row
        items = await self._get_order_items(order.id)
        return {
            "id": order.id,
            "club_id": order.club_id,
            "user_id": order.user_id,
            "status": order.status,
            "total_amount": order.total_amount,
            "notes": order.notes,
            "created_at": order.created_at,
            "items": items,
            "user_name": user_name,
        }

    async def create_order(self, user_id: UUID, items_input: list[dict], notes: str | None) -> dict:
        total = Decimal("0")
        order_items_data = []

        for item_input in items_input:
            item_stmt = select(MerchandiseItem).where(MerchandiseItem.id == item_input["item_id"])
            item_result = await self.db.execute(item_stmt)
            item = item_result.scalar_one_or_none()
            if not item:
                continue

            unit_price = item.base_price
            variant_name = None

            if item_input.get("variant_id"):
                var_stmt = select(MerchandiseVariant).where(
                    MerchandiseVariant.id == item_input["variant_id"]
                )
                var_result = await self.db.execute(var_stmt)
                variant = var_result.scalar_one_or_none()
                if variant:
                    unit_price += variant.price_adjustment
                    variant_name = variant.name

            total += unit_price * item_input["quantity"]
            order_items_data.append({
                "item_id": item.id,
                "variant_id": item_input.get("variant_id"),
                "quantity": item_input["quantity"],
                "unit_price": unit_price,
                "item_name": item.name,
                "variant_name": variant_name,
            })

        order = MerchandiseOrder(
            club_id=self.club_id,
            user_id=user_id,
            total_amount=total,
            notes=notes,
        )
        self.db.add(order)
        await self.db.flush()

        for oi_data in order_items_data:
            oi = MerchandiseOrderItem(order_id=order.id, **oi_data)
            self.db.add(oi)
        await self.db.flush()
        await self.db.refresh(order)

        return await self.get_by_id(order.id)

    async def update_status(self, order_id: UUID, status: str) -> dict | None:
        stmt = select(MerchandiseOrder).where(MerchandiseOrder.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            return None
        order.status = status
        await self.db.flush()
        return await self.get_by_id(order_id)

    async def cancel_order(self, order_id: UUID) -> dict | None:
        return await self.update_status(order_id, "cancelled")

    async def get_order_summary(self) -> dict:
        base = select(func.count()).where(MerchandiseOrder.club_id == self.club_id)
        total = (await self.db.execute(base)).scalar_one()
        pending = (await self.db.execute(
            base.where(MerchandiseOrder.status == "pending")
        )).scalar_one()
        confirmed = (await self.db.execute(
            base.where(MerchandiseOrder.status == "confirmed")
        )).scalar_one()
        revenue_stmt = (
            select(func.coalesce(func.sum(MerchandiseOrder.total_amount), 0))
            .where(
                MerchandiseOrder.club_id == self.club_id,
                MerchandiseOrder.status.notin_(["cancelled"]),
            )
        )
        revenue = (await self.db.execute(revenue_stmt)).scalar_one()
        return {
            "total_orders": total,
            "pending_orders": pending,
            "confirmed_orders": confirmed,
            "total_revenue": revenue,
        }

    async def _get_order_items(self, order_id: UUID) -> list[dict]:
        stmt = select(MerchandiseOrderItem).where(MerchandiseOrderItem.order_id == order_id)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        return [
            {
                "id": oi.id,
                "item_id": oi.item_id,
                "variant_id": oi.variant_id,
                "quantity": oi.quantity,
                "unit_price": oi.unit_price,
                "item_name": oi.item_name,
                "variant_name": oi.variant_name,
            }
            for oi in items
        ]
