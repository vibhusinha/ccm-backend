from fastapi import APIRouter

from app.api.v1 import (
    announcements,
    auth,
    availability,
    clubs,
    faqs,
    fee_config,
    fixture_series,
    fixture_types,
    health,
    lifecycle,
    matches,
    media,
    members,
    merchandise,
    messaging,
    navigation,
    notifications,
    payments,
    play_cricket,
    players,
    platform,
    profiles,
    recommendations,
    registration,
    roles,
    scoring,
    seasons,
    selections,
    statistics,
    teams,
)

api_router = APIRouter(prefix="/api/v1")

# Public
api_router.include_router(health.router)

# Auth
api_router.include_router(auth.router)

# Registration (approved-clubs is public, rest require auth)
api_router.include_router(registration.router)
api_router.include_router(registration.club_registrations_router)

# Profiles
api_router.include_router(profiles.router)

# Roles & Permissions
api_router.include_router(roles.router)
api_router.include_router(roles.permissions_router)
api_router.include_router(roles.user_perms_router)
api_router.include_router(roles.members_router)
api_router.include_router(roles.clubs_roles_router)

# Platform admin
api_router.include_router(platform.router)
api_router.include_router(navigation.router)

# Club-scoped resources
api_router.include_router(clubs.router)
api_router.include_router(members.router)
api_router.include_router(seasons.router)
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(matches.router)
api_router.include_router(matches.fixtures_router)
api_router.include_router(availability.router)
api_router.include_router(availability.bulk_router)
api_router.include_router(selections.router)
api_router.include_router(fixture_types.router)
api_router.include_router(fixture_types.type_action_router)
api_router.include_router(fixture_series.router)
api_router.include_router(announcements.router)
api_router.include_router(faqs.router)

# Payments & Finance
api_router.include_router(payments.router)
api_router.include_router(payments.player_payments_router)
api_router.include_router(payments.payment_actions_router)
api_router.include_router(payments.stripe_router)
api_router.include_router(fee_config.router)

# Notifications
api_router.include_router(notifications.router)
api_router.include_router(notifications.notification_actions_router)
api_router.include_router(notifications.reminders_router)
api_router.include_router(notifications.push_tokens_router)

# Scoring & Statistics
api_router.include_router(scoring.router)
api_router.include_router(scoring.club_router)
api_router.include_router(scoring.innings_router)
api_router.include_router(statistics.router)

# Lifecycle
api_router.include_router(lifecycle.router)
api_router.include_router(lifecycle.club_router)
api_router.include_router(lifecycle.player_router)

# Recommendations
api_router.include_router(recommendations.match_router)
api_router.include_router(recommendations.club_router)
api_router.include_router(recommendations.player_router)
api_router.include_router(recommendations.override_router)
api_router.include_router(recommendations.fixture_router)

# Messaging
api_router.include_router(messaging.channel_router)
api_router.include_router(messaging.message_channel_router)
api_router.include_router(messaging.message_action_router)
api_router.include_router(messaging.poll_option_router)
api_router.include_router(messaging.poll_action_router)

# Merchandise
api_router.include_router(merchandise.club_router)
api_router.include_router(merchandise.item_router)
api_router.include_router(merchandise.variant_router)
api_router.include_router(merchandise.order_router)
api_router.include_router(merchandise.image_router)

# Media
api_router.include_router(media.club_router)
api_router.include_router(media.gallery_router)
api_router.include_router(media.item_router)
api_router.include_router(media.tag_router)

# Play-Cricket Integration
api_router.include_router(play_cricket.router)
