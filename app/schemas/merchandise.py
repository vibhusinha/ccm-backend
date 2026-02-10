from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


# --- Categories ---

class MerchCategoryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    name: str
    description: str | None
    display_order: int
    is_active: bool


class MerchCategoryCreate(BaseModel):
    name: str
    description: str | None = None
    display_order: int = 0


class MerchCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


# --- Items ---

class MerchItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    category_id: UUID | None
    name: str
    description: str | None
    base_price: Decimal
    image_url: str | None
    is_active: bool
    stock_quantity: int
    low_stock_threshold: int
    category_name: str | None = None


class MerchItemCreate(BaseModel):
    category_id: UUID | None = None
    name: str
    description: str | None = None
    base_price: Decimal
    image_url: str | None = None
    stock_quantity: int = 0
    low_stock_threshold: int = 5


class MerchItemUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    base_price: Decimal | None = None
    image_url: str | None = None
    is_active: bool | None = None
    stock_quantity: int | None = None
    low_stock_threshold: int | None = None


# --- Variants ---

class MerchVariantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    item_id: UUID
    name: str
    sku: str | None
    price_adjustment: Decimal
    stock_quantity: int
    is_active: bool


class MerchVariantCreate(BaseModel):
    name: str
    sku: str | None = None
    price_adjustment: Decimal = Decimal("0")
    stock_quantity: int = 0


class MerchVariantUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    price_adjustment: Decimal | None = None
    stock_quantity: int | None = None
    is_active: bool | None = None


# --- Orders ---

class OrderItemInput(BaseModel):
    item_id: UUID
    variant_id: UUID | None = None
    quantity: int


class MerchOrderCreate(BaseModel):
    items: list[OrderItemInput]
    notes: str | None = None


class OrderItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    item_id: UUID | None
    variant_id: UUID | None
    quantity: int
    unit_price: Decimal
    item_name: str
    variant_name: str | None


class MerchOrderRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    user_id: UUID | None
    status: str
    total_amount: Decimal
    notes: str | None
    created_at: datetime | None = None
    items: list[OrderItemRead] = []
    user_name: str | None = None


class OrderStatusUpdate(BaseModel):
    status: str


# --- Summaries ---

class MerchSummary(BaseModel):
    total_items: int
    active_items: int
    total_categories: int
    low_stock_count: int
    total_orders: int
    pending_orders: int


class OrderSummary(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    total_revenue: Decimal


class MerchImageDelete(BaseModel):
    image_url: str
