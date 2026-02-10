import copy
import uuid

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/navigation", tags=["navigation"])

# Hardcoded default navigation items matching the frontend's expected shape.
# In-memory store — persisted across requests but not across restarts.
DEFAULT_NAV_ITEMS = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "home")),
        "key": "home",
        "label": "Home",
        "route": "/(tabs)",
        "icon": "Home",
        "display_order": 1,
        "is_enabled": True,
        "visible_to_roles": ["super_admin", "clubadmin", "secretary", "treasurer", "captain", "vice_captain", "player", "sponsor"],
        "hide_from_mobile_tabs": False,
        "hide_from_desktop_sidebar": False,
        "nav_group": "main",
        "description": "Dashboard home",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "schedule")),
        "key": "schedule",
        "label": "Schedule",
        "route": "/(tabs)/schedule",
        "icon": "Calendar",
        "display_order": 2,
        "is_enabled": True,
        "visible_to_roles": ["super_admin", "clubadmin", "secretary", "treasurer", "captain", "vice_captain", "player", "sponsor"],
        "hide_from_mobile_tabs": False,
        "hide_from_desktop_sidebar": False,
        "nav_group": "main",
        "description": "Match schedule and availability",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "members")),
        "key": "members",
        "label": "Members",
        "route": "/(tabs)/members",
        "icon": "Users",
        "display_order": 3,
        "is_enabled": True,
        "visible_to_roles": ["super_admin", "clubadmin", "secretary", "treasurer", "captain", "vice_captain", "player"],
        "hide_from_mobile_tabs": False,
        "hide_from_desktop_sidebar": False,
        "nav_group": "main",
        "description": "Club members",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "payments")),
        "key": "payments",
        "label": "Payments",
        "route": "/(tabs)/payments",
        "icon": "CreditCard",
        "display_order": 4,
        "is_enabled": True,
        "visible_to_roles": ["super_admin", "clubadmin", "secretary", "treasurer", "captain", "vice_captain", "player"],
        "hide_from_mobile_tabs": False,
        "hide_from_desktop_sidebar": False,
        "nav_group": "main",
        "description": "Payment management",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "stats")),
        "key": "stats",
        "label": "Stats",
        "route": "/(tabs)/stats",
        "icon": "BarChart3",
        "display_order": 5,
        "is_enabled": True,
        "visible_to_roles": ["super_admin", "clubadmin", "secretary", "treasurer", "captain", "vice_captain", "player"],
        "hide_from_mobile_tabs": False,
        "hide_from_desktop_sidebar": False,
        "nav_group": "main",
        "description": "Club statistics",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "admin")),
        "key": "admin",
        "label": "Admin",
        "route": "/(tabs)/admin",
        "icon": "Settings",
        "display_order": 6,
        "is_enabled": True,
        "visible_to_roles": ["super_admin", "clubadmin", "secretary", "treasurer"],
        "hide_from_mobile_tabs": True,
        "hide_from_desktop_sidebar": False,
        "nav_group": "admin",
        "description": "Club administration",
    },
]


def _find_by_key(key: str) -> dict | None:
    return next((item for item in DEFAULT_NAV_ITEMS if item["key"] == key), None)


def _find_by_id(item_id: str) -> dict | None:
    return next((item for item in DEFAULT_NAV_ITEMS if item["id"] == item_id), None)


@router.get("/items")
async def get_navigation_items(
    role: str | None = Query(None),
) -> list[dict]:
    """Return navigation items, optionally filtered by role."""
    if role:
        return [
            item
            for item in DEFAULT_NAV_ITEMS
            if item["is_enabled"] and role in item["visible_to_roles"]
        ]
    return [item for item in DEFAULT_NAV_ITEMS if item["is_enabled"]]


@router.get("/items/all")
async def get_all_navigation_items() -> list[dict]:
    """Return all navigation items including disabled ones (admin view)."""
    return DEFAULT_NAV_ITEMS


class ReorderInput(BaseModel):
    keys: list[str]


@router.post("/reorder")
async def reorder_navigation_items(body: ReorderInput) -> list[dict]:
    """Reorder navigation items by providing keys in desired order."""
    for i, key in enumerate(body.keys):
        item = _find_by_key(key)
        if item:
            item["display_order"] = i + 1
    DEFAULT_NAV_ITEMS.sort(key=lambda x: x["display_order"])
    return DEFAULT_NAV_ITEMS


@router.post("/items/{key}/toggle")
async def toggle_navigation_item(key: str) -> dict:
    """Toggle a navigation item's enabled status."""
    item = _find_by_key(key)
    if not item:
        return {"error": "Item not found"}
    item["is_enabled"] = not item["is_enabled"]
    return item


class NavItemUpdate(BaseModel):
    label: str | None = None
    icon: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    hide_from_mobile_tabs: bool | None = None
    hide_from_desktop_sidebar: bool | None = None
    visible_to_roles: list[str] | None = None


@router.patch("/items/{key}")
async def update_navigation_item(key: str, body: NavItemUpdate) -> dict:
    """Update a navigation item by key."""
    item = _find_by_key(key)
    if not item:
        return {"error": "Item not found"}
    for field, value in body.model_dump(exclude_unset=True).items():
        item[field] = value
    return item


@router.patch("/items/by-id/{item_id}")
async def update_navigation_item_by_id(item_id: str, body: NavItemUpdate) -> dict:
    """Update a navigation item by ID."""
    item = _find_by_id(item_id)
    if not item:
        return {"error": "Item not found"}
    for field, value in body.model_dump(exclude_unset=True).items():
        item[field] = value
    return item


class BatchReorderInput(BaseModel):
    items: list[dict]  # [{key, display_order}]


@router.post("/batch-reorder")
async def batch_reorder_navigation_items(body: BatchReorderInput) -> list[dict]:
    """Batch reorder navigation items."""
    for entry in body.items:
        item = _find_by_key(entry.get("key", ""))
        if item and "display_order" in entry:
            item["display_order"] = entry["display_order"]
    DEFAULT_NAV_ITEMS.sort(key=lambda x: x["display_order"])
    return DEFAULT_NAV_ITEMS
