from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import AsyncSessionLocal
from database.models import Message as DBMessage

router = Router()

# Твой file_id логотипа (самый большой вариант)
LOGO_FILE_ID = "AgACAgIAAxkBAAEb7GpprxxOR_h2OzbuPXFX6WacAQk94wACGhtrGyADeEmb6_RTwguhAwEAAwIAA3kAAzoE"


@router.callback_query(F.data.startswith("reply_"))
async def start_reply(callback: CallbackQuery, state: FSMContext):
    print(f"[DEBUG] Нажата кнопка reply_, data: {callback.data}")

    try:
        message_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("<b>Ошибка обработки кнопки</b>", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        msg = await session.get(DBMessage, message_id)
        if not msg:
            await callback.answer("<b>Вопрос не найден</b>", show_alert=True)
            return

        await state.update_data(
            reply_to=msg.id,
            sender_id=msg.sender_id
        )
        print(f"[DEBUG] Состояние reply_state установлено для sender_id={msg.sender_id}")

        await callback.message.answer(
            "<b>Напишите ответ анонимно:</b>\n\n"
            "Ваше сообщение будет отправлено отправителю полностью анонимно.\n\n"
            "<i>Просто напишите текст и отправьте.</i>",
            parse_mode="HTML"
        )
        await state.set_state("reply_state")
        await callback.answer()


@router.message(StateFilter("reply_state"), F.text)
async def send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    sender_id = data.get("sender_id")

    if not sender_id:
        await message.answer(
            "<b>Ошибка:</b> не найден получатель.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    try:
        # Ответ отправителю (анонимно)
        await message.bot.send_photo(
            chat_id=sender_id,
            photo=LOGO_FILE_ID,
            caption=(
                "<b>Получен анонимный ответ:</b>\n\n"
                f"<code>{message.text}</code>\n\n"
                "<i>Ответ пришёл через @AnonMokiichBot</i>"
            ),
            parse_mode="HTML"
        )

        # Подтверждение автору ответа
        await message.answer(
            "<b>Ответ успешно отправлен анонимно!</b> 🎉",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(
            "<b>Не удалось отправить ответ.</b>\n"
            "Возможно, пользователь заблокировал бота или произошла ошибка.",
            parse_mode="HTML"
        )
        print(f"Ошибка отправки ответа: {e}")

    await state.clear()


@router.message(StateFilter("reply_state"))
async def wrong_input_in_reply_state(message: Message, state: FSMContext):
    """
    Ловит любые сообщения в состоянии reply_state, кроме обычного текста
    (например, стикеры, фото, голосовые и т.д.)
    """
    await message.answer(
        "<b>Пожалуйста, напишите текстовый ответ.</b>\n\n"
        "Стикеры, фото, голосовые и другие вложения пока не поддерживаются.",
        parse_mode="HTML"
    )
    # состояние НЕ очищаем — продолжаем ждать текст