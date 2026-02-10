from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.payment import (
    ClubFinanceSummary,
    PaymentRead,
    PaymentReconcile,
    PaymentReduce,
    PaymentStatusUpdate,
    PaymentWaive,
    PlayerPaymentSummary,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/clubs/{club_id}", tags=["payments"])
player_payments_router = APIRouter(prefix="/players/{player_id}", tags=["payments"])
payment_actions_router = APIRouter(prefix="/payments/{payment_id}", tags=["payments"])


@router.get("/payments/", response_model=list[PaymentRead])
async def list_payments(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PaymentRead]:
    require_admin(current_user, club_id)
    service = PaymentService(db, club_id)
    payments = await service.get_all()
    return [PaymentRead.model_validate(p) for p in payments]


@router.get("/finance-summary", response_model=ClubFinanceSummary)
async def get_finance_summary(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClubFinanceSummary:
    require_admin(current_user, club_id)
    service = PaymentService(db, club_id)
    summary = await service.get_finance_summary()
    return ClubFinanceSummary(**summary)


@router.get("/player-payment-summaries", response_model=list[PlayerPaymentSummary])
async def get_player_payment_summaries(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlayerPaymentSummary]:
    require_admin(current_user, club_id)
    service = PaymentService(db, club_id)
    summaries = await service.get_player_payment_summaries()
    return [PlayerPaymentSummary(**s) for s in summaries]


@player_payments_router.get("/payments/", response_model=list[PaymentRead])
async def get_player_payments(
    player_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PaymentRead]:
    # Look up the player to get club_id for permission check
    from app.models.player import Player

    from sqlalchemy import select

    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise NotFoundError("Player not found")
    require_member(current_user, player.club_id)
    service = PaymentService(db, player.club_id)
    payments = await service.get_for_player(player_id)
    return [PaymentRead.model_validate(p) for p in payments]


@player_payments_router.get("/payments/pending", response_model=list[PaymentRead])
async def get_pending_payments(
    player_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PaymentRead]:
    from app.models.player import Player

    from sqlalchemy import select

    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise NotFoundError("Player not found")
    require_member(current_user, player.club_id)
    service = PaymentService(db, player.club_id)
    payments = await service.get_pending_for_player(player_id)
    return [PaymentRead.model_validate(p) for p in payments]


@payment_actions_router.post("/waive", response_model=PaymentRead)
async def waive_payment(
    payment_id: Annotated[UUID, Path()],
    body: PaymentWaive,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentRead:
    from app.models.payment import Payment

    from sqlalchemy import select

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")
    require_admin(current_user, payment.club_id)
    service = PaymentService(db, payment.club_id)
    updated = await service.waive_payment(payment_id, body.reason)
    return PaymentRead.model_validate(updated)


@payment_actions_router.post("/reduce", response_model=PaymentRead)
async def reduce_payment(
    payment_id: Annotated[UUID, Path()],
    body: PaymentReduce,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentRead:
    from app.models.payment import Payment

    from sqlalchemy import select

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")
    require_admin(current_user, payment.club_id)
    service = PaymentService(db, payment.club_id)
    updated = await service.reduce_payment(payment_id, body.new_amount, body.reason)
    return PaymentRead.model_validate(updated)


@payment_actions_router.post("/reconcile", response_model=PaymentRead)
async def reconcile_payment(
    payment_id: Annotated[UUID, Path()],
    body: PaymentReconcile,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentRead:
    from app.models.payment import Payment

    from sqlalchemy import select

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")
    require_admin(current_user, payment.club_id)
    service = PaymentService(db, payment.club_id)
    updated = await service.reconcile_payment(
        payment_id, body.bank_reference, body.received_date
    )
    return PaymentRead.model_validate(updated)


@payment_actions_router.patch("/", response_model=PaymentRead)
async def update_payment_status(
    payment_id: Annotated[UUID, Path()],
    body: PaymentStatusUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentRead:
    from app.models.payment import Payment

    from sqlalchemy import select

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")
    require_admin(current_user, payment.club_id)
    service = PaymentService(db, payment.club_id)
    updated = await service.update_status(payment_id, body.status, body.paid_date)
    return PaymentRead.model_validate(updated)
