import uuid

from fastapi import APIRouter, Query

router = APIRouter(prefix="/navigation", tags=["navigation"])

# Hardcoded default navigation items matching the frontend's expected shape.
# This is a stub — a full navigation management system can be built later.
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
