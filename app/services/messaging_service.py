from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.message import Message
from app.models.message_reaction import MessageReaction
from app.models.poll import Poll
from app.models.poll_option import PollOption
from app.models.poll_vote import PollVote
from app.models.profile import Profile


class MessagingService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    # --- Channels ---

    async def get_channels(self) -> list[Channel]:
        stmt = select(Channel).where(Channel.club_id == self.club_id).order_by(Channel.created_at)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # --- Messages ---

    async def get_messages(
        self, channel_id: UUID, *, offset: int = 0, limit: int = 50
    ) -> list[dict]:
        stmt = (
            select(Message, Profile.display_name.label("sender_name"))
            .outerjoin(Profile, Message.sender_id == Profile.id)
            .where(Message.channel_id == channel_id, Message.is_deleted.is_(False))
            .order_by(Message.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        messages = []
        for msg, sender_name in rows:
            # Get reactions for this message
            react_stmt = (
                select(
                    MessageReaction.emoji,
                    func.count().label("count"),
                )
                .where(MessageReaction.message_id == msg.id)
                .group_by(MessageReaction.emoji)
            )
            react_result = await self.db.execute(react_stmt)
            reactions = [{"emoji": r.emoji, "count": r.count} for r in react_result.all()]

            messages.append({
                "id": msg.id,
                "channel_id": msg.channel_id,
                "sender_id": msg.sender_id,
                "content": msg.content,
                "is_pinned": msg.is_pinned,
                "is_deleted": msg.is_deleted,
                "created_at": msg.created_at,
                "sender_name": sender_name,
                "reactions": reactions,
            })
        return messages

    async def send_message(self, channel_id: UUID, sender_id: UUID, content: str) -> Message:
        msg = Message(channel_id=channel_id, sender_id=sender_id, content=content)
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def toggle_pin(self, message_id: UUID, is_pinned: bool) -> Message:
        stmt = select(Message).where(Message.id == message_id)
        result = await self.db.execute(stmt)
        msg = result.scalar_one_or_none()
        if msg:
            msg.is_pinned = is_pinned
            await self.db.flush()
            await self.db.refresh(msg)
        return msg

    async def delete_message(self, message_id: UUID) -> bool:
        stmt = select(Message).where(Message.id == message_id)
        result = await self.db.execute(stmt)
        msg = result.scalar_one_or_none()
        if not msg:
            return False
        msg.is_deleted = True
        await self.db.flush()
        return True

    async def add_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> dict:
        # Toggle: remove if exists, add if not
        stmt = select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == emoji,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.flush()
            return {"action": "removed"}
        reaction = MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji)
        self.db.add(reaction)
        await self.db.flush()
        return {"action": "added"}

    # --- Polls ---

    async def get_polls(self, current_user_id: UUID) -> list[dict]:
        stmt = (
            select(Poll, Profile.display_name.label("creator_name"))
            .outerjoin(Profile, Poll.created_by == Profile.id)
            .where(Poll.club_id == self.club_id)
            .order_by(Poll.created_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        polls = []
        for poll, creator_name in rows:
            options = await self._get_poll_options(poll.id, current_user_id)
            polls.append({
                "id": poll.id,
                "channel_id": poll.channel_id,
                "club_id": poll.club_id,
                "created_by": poll.created_by,
                "question": poll.question,
                "is_closed": poll.is_closed,
                "allow_multiple": poll.allow_multiple,
                "created_at": poll.created_at,
                "options": options,
                "creator_name": creator_name,
            })
        return polls

    async def create_poll(
        self, channel_id: UUID, created_by: UUID, question: str,
        options: list[dict], allow_multiple: bool = False,
    ) -> dict:
        poll = Poll(
            channel_id=channel_id,
            club_id=self.club_id,
            created_by=created_by,
            question=question,
            allow_multiple=allow_multiple,
        )
        self.db.add(poll)
        await self.db.flush()

        for i, opt in enumerate(options):
            option = PollOption(poll_id=poll.id, text=opt["text"], display_order=i)
            self.db.add(option)
        await self.db.flush()
        await self.db.refresh(poll)

        poll_options = await self._get_poll_options(poll.id, created_by)
        return {
            "id": poll.id,
            "channel_id": poll.channel_id,
            "club_id": poll.club_id,
            "created_by": poll.created_by,
            "question": poll.question,
            "is_closed": poll.is_closed,
            "allow_multiple": poll.allow_multiple,
            "created_at": poll.created_at,
            "options": poll_options,
        }

    async def vote_on_poll(self, option_id: UUID, user_id: UUID) -> dict:
        # Get the poll for this option
        stmt = (
            select(PollOption, Poll)
            .join(Poll, PollOption.poll_id == Poll.id)
            .where(PollOption.id == option_id)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if not row:
            return {"success": False, "error": "Option not found"}
        option, poll = row

        if poll.is_closed:
            return {"success": False, "error": "Poll is closed"}

        # Check if already voted on this option
        existing = await self.db.execute(
            select(PollVote).where(
                PollVote.poll_option_id == option_id,
                PollVote.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            # Remove vote (toggle)
            await self.db.execute(
                delete(PollVote).where(
                    PollVote.poll_option_id == option_id,
                    PollVote.user_id == user_id,
                )
            )
            await self.db.flush()
            return {"success": True, "action": "removed"}

        # If not allow_multiple, remove existing votes on other options
        if not poll.allow_multiple:
            all_options = await self.db.execute(
                select(PollOption.id).where(PollOption.poll_id == poll.id)
            )
            option_ids = [r[0] for r in all_options.all()]
            await self.db.execute(
                delete(PollVote).where(
                    PollVote.poll_option_id.in_(option_ids),
                    PollVote.user_id == user_id,
                )
            )

        vote = PollVote(poll_option_id=option_id, user_id=user_id)
        self.db.add(vote)
        await self.db.flush()
        return {"success": True, "action": "added"}

    async def close_poll(self, poll_id: UUID) -> Poll:
        stmt = select(Poll).where(Poll.id == poll_id)
        result = await self.db.execute(stmt)
        poll = result.scalar_one_or_none()
        if poll:
            poll.is_closed = True
            await self.db.flush()
            await self.db.refresh(poll)
        return poll

    async def _get_poll_options(self, poll_id: UUID, current_user_id: UUID) -> list[dict]:
        stmt = (
            select(PollOption)
            .where(PollOption.poll_id == poll_id)
            .order_by(PollOption.display_order)
        )
        result = await self.db.execute(stmt)
        options = list(result.scalars().all())

        option_data = []
        for opt in options:
            count_stmt = select(func.count()).where(PollVote.poll_option_id == opt.id)
            count_result = await self.db.execute(count_stmt)
            vote_count = count_result.scalar_one()

            voted_stmt = select(PollVote).where(
                PollVote.poll_option_id == opt.id,
                PollVote.user_id == current_user_id,
            )
            voted_result = await self.db.execute(voted_stmt)
            voted_by_me = voted_result.scalar_one_or_none() is not None

            option_data.append({
                "id": opt.id,
                "text": opt.text,
                "display_order": opt.display_order,
                "vote_count": vote_count,
                "voted_by_me": voted_by_me,
            })
        return option_data

    # --- Helper to get channel's club_id ---

    @staticmethod
    async def get_channel_club_id(db: AsyncSession, channel_id: UUID) -> UUID | None:
        stmt = select(Channel.club_id).where(Channel.id == channel_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_message_channel_id(db: AsyncSession, message_id: UUID) -> UUID | None:
        stmt = select(Message.channel_id).where(Message.id == message_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
