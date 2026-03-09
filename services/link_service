# services/link_service.py (вариант 2)
import shortuuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import AskLink


async def create_new_link(
        session: AsyncSession,
        owner_id: int,
        secret: str,  # ← добавлен параметр
        destination_type: str,
        destination_id: int | None = None,
        reveal_in_channel: bool = False
) -> AskLink:
    link = AskLink(
        owner_id=owner_id,
        secret=secret,
        destination_type=destination_type,
        destination_id=destination_id,
        reveal_in_channel=reveal_in_channel,
        is_active=True
    )

    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


# остальные функции без изменений
async def get_link_by_secret(session: AsyncSession, secret: str) -> AskLink | None:
    stmt = select(AskLink).where(AskLink.secret == secret)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_links(session: AsyncSession, owner_id: int):
    stmt = select(AskLink).where(AskLink.owner_id == owner_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def deactivate_link(session: AsyncSession, link_id: int):
    stmt = select(AskLink).where(AskLink.id == link_id)
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    if link:
        link.is_active = False
        await session.commit()
