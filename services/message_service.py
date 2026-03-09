from aiogram import Bot
from database.models import AskLink, Message as DBMessage
from config import ADMIN_IDS
from keyboards.inline import question_actions_kb

# File ID логотипа
LOGO_FILE_ID = "AgACAgIAAxkBAAEb7GpprxxOR_h2OzbuPXFX6WacAQk94wACGhtrGyADeEmb6_RTwguhAwEAAwIAA3kAAzoE"


async def send_question(bot: Bot, link: AskLink, db_msg: DBMessage, is_premium: bool):
    """
    Отправляет анонимный вопрос владельцу в личку и (если нужно) в канал.
    Сообщение всегда с логотипом сверху.
    """
    is_admin = link.owner_id in ADMIN_IDS
    show_sender = is_premium or is_admin

    # Формируем информацию об отправителе
    sender_info = "аноним"

    if show_sender:
        if db_msg.sender_username:
            sender_info = f"@{db_msg.sender_username}"
        elif db_msg.sender_first_name:
            name = f"{db_msg.sender_first_name} {db_msg.sender_last_name or ''}".strip()
            sender_info = f"от {name}" if name else f"от пользователя (ID {db_msg.sender_id})"
        else:
            sender_info = f"от пользователя (ID {db_msg.sender_id})"

    # Текст для личных сообщений владельцу
    text_private = (
        "<b>Кто-то отправил тебе анонимное сообщение:</b>\n\n"
        f"<code>{db_msg.text}</code>\n\n"
        f"<b>Отправитель: {sender_info}</b>\n"
        "<b>👈 Свайпни, чтобы ответить на него.</b>"
    )

    kb = question_actions_kb(db_msg.id)

    # Отправка владельцу в личку
    await bot.send_photo(
        chat_id=link.owner_id,
        photo=LOGO_FILE_ID,
        caption=text_private,
        parse_mode="HTML",
        reply_markup=kb.as_markup(),
        disable_notification=False
    )

    # Отправка в канал (если включено)
    if link.destination_type == "channel_both" and link.destination_id:
        # Текст для канала — без клавиатуры и без «свайпни»
        text_channel = (
            "<b>Анонимное сообщение:</b>\n\n"
            f"<code>{db_msg.text}</code>\n\n"
        )

        # Добавляем отправителя только если разрешено
        if link.reveal_in_channel and show_sender:
            text_channel += f"<b>Отправитель: {sender_info}</b>\n\n"

        text_channel += "<b>✉️ Анонимное сообщение через @AnonMokiichBot</b>"

        await bot.send_photo(
            chat_id=link.destination_id,
            photo=LOGO_FILE_ID,
            caption=text_channel,
            parse_mode="HTML",          # теперь тоже HTML
            disable_notification=True
        )