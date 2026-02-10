from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.merchandise import (
    MerchCategoryCreate,
    MerchCategoryRead,
    MerchCategoryUpdate,
    MerchImageDelete,
    MerchItemCreate,
    MerchItemRead,
    MerchItemUpdate,
    MerchOrderCreate,
    MerchOrderRead,
    MerchSummary,
    MerchVariantCreate,
    MerchVariantRead,
    MerchVariantUpdate,
    OrderStatusUpdate,
    OrderSummary,
)
from app.services.merchandise_service import (
    MerchCategoryService,
    MerchItemService,
    MerchOrderService,
    MerchVariantService,
)

# Club-scoped routes
club_router = APIRouter(prefix="/clubs/{club_id}/merchandise", tags=["merchandise"])

# Item-scoped routes
item_router = APIRouter(prefix="/merchandise/items/{item_id}", tags=["merchandise"])

# Variant-scoped routes
variant_router = APIRouter(prefix="/merchandise/variants/{variant_id}", tags=["merchandise"])

# Order-scoped routes
order_router = APIRouter(prefix="/merchandise/orders/{order_id}", tags=["merchandise"])

# Image routes
image_router = APIRouter(prefix="/merchandise/images", tags=["merchandise"])


# --- Categories ---

@club_router.get("/categories", response_model=list[MerchCategoryRead])
async def list_categories(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MerchCategoryRead]:
    require_member(current_user, club_id)
    service = MerchCategoryService(db, club_id)
    categories = await service.get_all()
    return [MerchCategoryRead.model_validate(c) for c in categories]


@club_router.post("/categories", response_model=MerchCategoryRead, status_code=201)
async def create_category(
    club_id: Annotated[UUID, Path()],
    body: MerchCategoryCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchCategoryRead:
    require_admin(current_user, club_id)
    service = MerchCategoryService(db, club_id)
    category = await service.create(**body.model_dump())
    return MerchCategoryRead.model_validate(category)


@club_router.patch("/categories/{category_id}", response_model=MerchCategoryRead)
async def update_category(
    club_id: Annotated[UUID, Path()],
    category_id: Annotated[UUID, Path()],
    body: MerchCategoryUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchCategoryRead:
    require_admin(current_user, club_id)
    service = MerchCategoryService(db, club_id)
    category = await service.update(category_id, **body.model_dump(exclude_unset=True))
    if not category:
        raise NotFoundError("Category not found")
    return MerchCategoryRead.model_validate(category)


@club_router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    club_id: Annotated[UUID, Path()],
    category_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = MerchCategoryService(db, club_id)
    if not await service.delete(category_id):
        raise NotFoundError("Category not found")


# --- Items ---

@club_router.get("/items", response_model=list[MerchItemRead])
async def list_items(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MerchItemRead]:
    require_member(current_user, club_id)
    service = MerchItemService(db, club_id)
    items = await service.get_all_with_category()
    return [MerchItemRead(**i) for i in items]


@club_router.post("/items", response_model=MerchItemRead, status_code=201)
async def create_item(
    club_id: Annotated[UUID, Path()],
    body: MerchItemCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchItemRead:
    require_admin(current_user, club_id)
    service = MerchItemService(db, club_id)
    item = await service.create(**body.model_dump())
    return MerchItemRead.model_validate(item)


@club_router.patch("/items/{item_id}", response_model=MerchItemRead)
async def update_item(
    club_id: Annotated[UUID, Path()],
    item_id: Annotated[UUID, Path()],
    body: MerchItemUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchItemRead:
    require_admin(current_user, club_id)
    service = MerchItemService(db, club_id)
    item = await service.update(item_id, **body.model_dump(exclude_unset=True))
    if not item:
        raise NotFoundError("Item not found")
    return MerchItemRead.model_validate(item)


@club_router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    club_id: Annotated[UUID, Path()],
    item_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = MerchItemService(db, club_id)
    if not await service.delete(item_id):
        raise NotFoundError("Item not found")


@item_router.get("/", response_model=MerchItemRead)
async def get_item(
    item_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchItemRead:
    from app.models.merchandise_item import MerchandiseItem
    from sqlalchemy import select

    stmt = select(MerchandiseItem).where(MerchandiseItem.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Item not found")
    require_member(current_user, item.club_id)
    return MerchItemRead.model_validate(item)


# --- Variants ---

@item_router.get("/variants", response_model=list[MerchVariantRead])
async def list_variants(
    item_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MerchVariantRead]:
    from app.models.merchandise_item import MerchandiseItem
    from sqlalchemy import select

    stmt = select(MerchandiseItem.club_id).where(MerchandiseItem.id == item_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Item not found")
    require_member(current_user, club_id)
    service = MerchVariantService(db)
    variants = await service.get_for_item(item_id)
    return [MerchVariantRead.model_validate(v) for v in variants]


@item_router.post("/variants", response_model=MerchVariantRead, status_code=201)
async def create_variant(
    item_id: Annotated[UUID, Path()],
    body: MerchVariantCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchVariantRead:
    from app.models.merchandise_item import MerchandiseItem
    from sqlalchemy import select

    stmt = select(MerchandiseItem.club_id).where(MerchandiseItem.id == item_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Item not found")
    require_admin(current_user, club_id)
    service = MerchVariantService(db)
    variant = await service.create(item_id, **body.model_dump())
    return MerchVariantRead.model_validate(variant)


@variant_router.patch("/", response_model=MerchVariantRead)
async def update_variant(
    variant_id: Annotated[UUID, Path()],
    body: MerchVariantUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchVariantRead:
    from app.models.merchandise_item import MerchandiseItem
    from app.models.merchandise_variant import MerchandiseVariant
    from sqlalchemy import select

    stmt = (
        select(MerchandiseItem.club_id)
        .join(MerchandiseVariant, MerchandiseVariant.item_id == MerchandiseItem.id)
        .where(MerchandiseVariant.id == variant_id)
    )
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Variant not found")
    require_admin(current_user, club_id)
    service = MerchVariantService(db)
    variant = await service.update(variant_id, **body.model_dump(exclude_unset=True))
    if not variant:
        raise NotFoundError("Variant not found")
    return MerchVariantRead.model_validate(variant)


@variant_router.delete("/", status_code=204)
async def delete_variant(
    variant_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    from app.models.merchandise_item import MerchandiseItem
    from app.models.merchandise_variant import MerchandiseVariant
    from sqlalchemy import select

    stmt = (
        select(MerchandiseItem.club_id)
        .join(MerchandiseVariant, MerchandiseVariant.item_id == MerchandiseItem.id)
        .where(MerchandiseVariant.id == variant_id)
    )
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Variant not found")
    require_admin(current_user, club_id)
    service = MerchVariantService(db)
    if not await service.delete(variant_id):
        raise NotFoundError("Variant not found")


# --- Low Stock & Summary ---

@club_router.get("/low-stock", response_model=list[MerchItemRead])
async def get_low_stock(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MerchItemRead]:
    require_admin(current_user, club_id)
    service = MerchItemService(db, club_id)
    items = await service.get_low_stock()
    return [MerchItemRead.model_validate(i) for i in items]


@club_router.get("/summary", response_model=MerchSummary)
async def get_summary(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchSummary:
    require_member(current_user, club_id)
    service = MerchItemService(db, club_id)
    summary = await service.get_summary()
    return MerchSummary(**summary)


# --- Orders ---

@club_router.get("/orders", response_model=list[MerchOrderRead])
async def list_orders(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MerchOrderRead]:
    require_admin(current_user, club_id)
    service = MerchOrderService(db, club_id)
    orders = await service.get_all()
    return [MerchOrderRead(**o) for o in orders]


@club_router.post("/orders", response_model=MerchOrderRead, status_code=201)
async def create_order(
    club_id: Annotated[UUID, Path()],
    body: MerchOrderCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchOrderRead:
    require_member(current_user, club_id)
    service = MerchOrderService(db, club_id)
    order = await service.create_order(
        current_user.user_id,
        [item.model_dump() for item in body.items],
        body.notes,
    )
    return MerchOrderRead(**order)


@club_router.get("/orders/summary", response_model=OrderSummary)
async def get_order_summary(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderSummary:
    require_admin(current_user, club_id)
    service = MerchOrderService(db, club_id)
    summary = await service.get_order_summary()
    return OrderSummary(**summary)


@order_router.get("/", response_model=MerchOrderRead)
async def get_order(
    order_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchOrderRead:
    from app.models.merchandise_order import MerchandiseOrder
    from sqlalchemy import select

    stmt = select(MerchandiseOrder.club_id).where(MerchandiseOrder.id == order_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Order not found")
    require_member(current_user, club_id)
    service = MerchOrderService(db, club_id)
    order = await service.get_by_id(order_id)
    if not order:
        raise NotFoundError("Order not found")
    return MerchOrderRead(**order)


@order_router.post("/cancel", response_model=MerchOrderRead)
async def cancel_order(
    order_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchOrderRead:
    from app.models.merchandise_order import MerchandiseOrder
    from sqlalchemy import select

    stmt = select(MerchandiseOrder.club_id).where(MerchandiseOrder.id == order_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Order not found")
    require_member(current_user, club_id)
    service = MerchOrderService(db, club_id)
    order = await service.cancel_order(order_id)
    if not order:
        raise NotFoundError("Order not found")
    return MerchOrderRead(**order)


@order_router.post("/status", response_model=MerchOrderRead)
async def update_order_status(
    order_id: Annotated[UUID, Path()],
    body: OrderStatusUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchOrderRead:
    from app.models.merchandise_order import MerchandiseOrder
    from sqlalchemy import select

    stmt = select(MerchandiseOrder.club_id).where(MerchandiseOrder.id == order_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Order not found")
    require_admin(current_user, club_id)
    service = MerchOrderService(db, club_id)
    order = await service.update_status(order_id, body.status)
    if not order:
        raise NotFoundError("Order not found")
    return MerchOrderRead(**order)


# --- Image Delete ---

@image_router.post("/delete")
async def delete_image(
    body: MerchImageDelete,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    # Stub: In production, this would delete from S3/storage
    return {"success": True, "deleted": body.image_url}
