from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from database.engine import AsyncSessionLocal
from database.models import AskLink, Message as DBMessage, User
from services.message_service import send_question
from states.create_link import AskQuestion

router = Router()


@router.message(AskQuestion.waiting_for_question, F.text)
async def receive_question(message: Message, state: FSMContext):
    """
    Основной хендлер получения анонимного вопроса от пользователя.
    Работает только в состоянии ожидания вопроса.
    """
    user_id = message.from_user.id
    print(f"[QUESTION] Получен вопрос от пользователя {user_id}")

    data = await state.get_data()
    link_id = data.get("link_id")

    if not link_id:
        await message.answer(
            "Сессия истекла или ссылка недействительна.\nНачните заново по вашей секретной ссылке.",
            parse_mode='HTML'
        )
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        try:
            # Получаем ссылку по ID
            stmt = select(AskLink).where(AskLink.id == link_id)
            result = await session.execute(stmt)
            link = result.scalar_one_or_none()

            if not link:
                await message.answer(
                    "<b>Ссылка не найдена.</b>",
                    parse_mode='HTML'
                )
                await state.clear()
                return

            if not link.is_active:
                await message.answer(
                    "<b>Эта приёмная больше не активна.</b>",
                    parse_mode='HTML'
                )
                await state.clear()
                return

            # Получаем владельца и его статус премиум
            stmt = select(User).where(User.id == link.owner_id)
            result = await session.execute(stmt)
            owner = result.scalar_one_or_none()

            is_premium = owner.is_premium if owner else False
            print(f"[QUESTION] Владелец: {link.owner_id}, премиум: {is_premium}")

            text = message.text.strip()
            if not text:
                await message.answer(
                    "<b>Пустой вопрос не отправляется.</b>\nНапишите текст.",
                    parse_mode='HTML'
                )
                return

            # Создаём запись в базе
            db_msg = DBMessage(
                link_id=link.id,
                sender_id=user_id,
                sender_username=message.from_user.username,
                sender_first_name=message.from_user.first_name,
                sender_last_name=message.from_user.last_name,
                text=text
            )
            session.add(db_msg)
            await session.commit()
            await session.refresh(db_msg)  # получаем свежий ID

            # Отправляем вопрос владельцу и в канал (если нужно)
            await send_question(message.bot, link, db_msg, is_premium)

            # Успешная отправка
            await message.answer(
                "<b>Ваш вопрос успешно отправлен анонимно! 🎉</b>",
                parse_mode='HTML'
            )
            await state.clear()

        except SQLAlchemyError as e:
            print(f"[ERROR] Ошибка базы данных при обработке вопроса: {e}")
            await message.answer(
                "<b>Произошла ошибка на сервере.</b>\nПопробуйте позже.",
                parse_mode='HTML'
            )
            await state.clear()

        except Exception as e:
            print(f"[ERROR] Неизвестная ошибка при обработке вопроса: {e}")
            await message.answer(
                "<b>Что-то пошло не так.</b>\nПопробуйте отправить вопрос ещё раз.",
                parse_mode='HTML'
            )
            # состояние НЕ очищаем — пусть пользователь попробует снова