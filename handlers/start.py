import shortuuid
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import AsyncSessionLocal
from database.models import AskLink, User
from services.link_service import create_new_link
from keyboards.inline import (
    destination_kb,
    confirm_kb,
    my_links_kb,
    link_actions_kb,
    reveal_in_channel_kb,
    back_button
)
from states.create_link import CreateLink, AskQuestion
from config import ADMIN_IDS

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("secret"):
        secret = args[1][6:]
        async with AsyncSessionLocal() as session:
            stmt = select(AskLink).where(AskLink.secret == secret)
            result = await session.execute(stmt)
            link = result.scalar_one_or_none()

            if link and link.is_active:
                await state.set_state(AskQuestion.waiting_for_question)
                await state.update_data(link_id=link.id)
                await message.answer(
                    "<b>📩 Отправь анонимное сообщение</b>\n\n"
                    "<b>Напишите сообщение ниже, и оно будет отправлено человеку, который поделился этой ссылкой.</b>\n\n"
                    "<b>⏱ Сообщение придёт через несколько секунд, а отправитель останется полностью анонимным.</b>",
                    parse_mode='HTML'
                )
                return

            await message.answer(
                "Эта ссылка недействительна или была отключена 😔",
                parse_mode='HTML'
            )
            return

    kb = InlineKeyboardBuilder()
    kb.button(text="✨ АНОНИМНАЯ ССЫЛКА", callback_data="create_link")
    kb.button(text="📋 Мои ссылки", callback_data="my_links")
    kb.button(text="💎 PREMIUM STATUS", callback_data="buy_premium")
    kb.adjust(1)

    await message.answer(
        "<b>Готов к анонимным вопросам? 👀</b>\n\n"
        "<b>🔗 Создай свою ссылку, и вперед!</b>\n\n"
        "<b>🌎 Добавь её в описание профиля Telegram, TikTok или Instagram и начинай получать анонимные сообщения прямо сейчас.</b>\n\n",
        reply_markup=kb.as_markup(),
        parse_mode='HTML'
    )


@router.callback_query(F.data == "create_link")
async def create_link_start(callback: CallbackQuery, state: FSMContext):
    kb = destination_kb()
    await callback.message.edit_text(
        "<b>Куда вы хотите получать все анонимные вопросы и сообщения?</b>",
        reply_markup=kb.as_markup(),
        parse_mode='HTML'
    )
    await state.set_state(CreateLink.choose_destination)


@router.callback_query(CreateLink.choose_destination)
async def choose_destination(callback: CallbackQuery, state: FSMContext):
    if callback.data == "dest_private":
        await state.update_data(destination_type="private", destination_id=None)
        await confirm_link_creation(callback, state)
    elif callback.data == "dest_channel_both":
        await state.update_data(destination_type="channel_both")
        await callback.message.edit_text(
            "<b>Введите @username канала или его числовой ID</b>\n"
            "(бот должен быть администратором канала с правом отправки сообщений):",
            reply_markup=back_button().as_markup(),
            parse_mode='HTML'
        )
        await state.set_state(CreateLink.enter_channel)


@router.message(CreateLink.enter_channel)
async def enter_channel(message: Message, state: FSMContext):
    channel = message.text.strip()
    chat_id = None

    if channel.startswith("@"):
        try:
            chat = await message.bot.get_chat(channel)
            chat_id = chat.id
        except Exception:
            await message.answer(
                "<b>Не удалось найти канал. Проверьте @username и убедитесь, что бот — администратор.</b>",
                parse_mode='HTML'
            )
            return
    else:
        try:
            chat_id = int(channel)
        except ValueError:
            await message.answer(
                "<b>Пожалуйста, введите корректный @username или числовой ID канала.</b>",
                parse_mode='HTML'
            )
            return

    await state.update_data(destination_id=chat_id)
    kb = reveal_in_channel_kb()
    await message.answer(
        "<b>Раскрывать имя/ник отправителя в канале?</b>\n\n"
        "Если <b>«Да»</b> — все увидят, кто именно написал.\n"
        "Если <b>«Нет»</b> — останется полная анонимность.",
        reply_markup=kb.as_markup(),
        parse_mode='HTML'
    )
    await state.set_state(CreateLink.choose_reveal)


@router.callback_query(CreateLink.choose_reveal)
async def choose_reveal(callback: CallbackQuery, state: FSMContext):
    await state.update_data(reveal_in_channel=(callback.data == "reveal_yes"))
    await confirm_link_creation(callback, state)


async def confirm_link_creation(obj, state: FSMContext):
    data = await state.get_data()
    destination = "только в личные сообщения вам" if data["destination_type"] == "private" else "в канал/группу + в личные сообщения"
    reveal = "с раскрытием отправителя" if data.get("reveal_in_channel") else "полностью анонимно"

    text = (
        "<b>Подтвердите создание ссылки:</b>\n\n"
        f"<b>Вопросы будут приходить:</b>\n"
        f"📌 {destination}\n"
        f"<b>В канале:</b>\n"
        f"📌 {reveal}\n\n"
        "<b>Всё верно?</b>"
    )

    kb = confirm_kb()

    if isinstance(obj, Message):
        await obj.answer(
            text,
            reply_markup=kb.as_markup(),
            parse_mode='HTML'
        )
    else:  # CallbackQuery
        await obj.message.edit_text(
            text,
            reply_markup=kb.as_markup(),
            parse_mode='HTML'
        )

    await state.set_state(CreateLink.confirm)


@router.callback_query(CreateLink.confirm, F.data == "confirm_create")
async def confirm_create(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    owner_id = callback.from_user.id
    secret = shortuuid.uuid()[:16]

    async with AsyncSessionLocal() as s:
        link = await create_new_link(
            s,
            owner_id=owner_id,
            secret=secret,
            destination_type=data["destination_type"],
            destination_id=data.get("destination_id"),
            reveal_in_channel=data.get("reveal_in_channel", False)
        )

    bot = await callback.bot.get_me()
    link_url = f"https://t.me/{bot.username}?start=secret{secret}"

    share_text = (
        "Напиши мне анонимно любой вопрос или мысль 😏\n"
        f"{link_url}"
    )

    kb = InlineKeyboardBuilder()
    kb.button(
        text="🔗 Поделиться ссылкой",
        switch_inline_query_current_chat=share_text
    )
    kb.button(text="← В главное меню", callback_data="back_to_main")
    kb.adjust(1)

    await callback.message.edit_text(
        "<b>🎉 Ссылка успешно создана!</b>\n\n"
        f"{link_url}\n\n"
        "Теперь её можно сразу разослать друзьям, подписчикам или в чаты.\n"
        "Нажми кнопку ниже, чтобы поделиться!",
        reply_markup=kb.as_markup(),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    await state.clear()


@router.callback_query(F.data.in_({"cancel", "back_to_main"}))
async def back_or_cancel(callback: CallbackQuery, state: FSMContext):
    """
    Универсальный хендлер для отмены / возврата в главное меню
    Работает из любого состояния
    """
    await state.clear()

    kb = InlineKeyboardBuilder()
    kb.button(text="✨ АНОНИМНАЯ ССЫЛКА", callback_data="create_link")
    kb.button(text="📋 Мои ссылки", callback_data="my_links")
    kb.button(text="💎 PREMIUM STATUS", callback_data="buy_premium")
    kb.adjust(1)

    text = "<b>Главное меню</b>\n\n<b>Выберите действие ниже:</b>"

    try:
        await callback.message.edit_text(
            text,
            reply_markup=kb.as_markup(),
            parse_mode='HTML'
        )
    except Exception:
        # Если сообщение старое / удалено
        await callback.message.answer(
            text,
            reply_markup=kb.as_markup(),
            parse_mode='HTML'
        )

    await callback.answer("Вернулись в главное меню")


@router.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery, state: FSMContext):
    # На всякий случай оставляем отдельно, но теперь он тоже через универсальный хендлер
    await back_or_cancel(callback, state)


@router.message(Command("mylinks"))
@router.callback_query(F.data == "my_links")
async def my_links(event: Message | CallbackQuery):
    user_id = event.from_user.id
    is_callback = isinstance(event, CallbackQuery)
    message = event.message if is_callback else event

    async with AsyncSessionLocal() as session:
        stmt = select(AskLink).where(AskLink.owner_id == user_id)
        result = await session.execute(stmt)
        links = result.scalars().all()

        if not links:
            text = (
                "<b>У вас пока нет созданных ссылок 😔</b>\n\n"
                "<b>Создайте первую прямо сейчас и начните получать анонимные вопросы!</b>"
            )
            kb = InlineKeyboardBuilder()
            kb.button(text="✨ Создать новую", callback_data="create_link")
            kb.button(text="Назад в меню", callback_data="back_to_main")
            kb.adjust(1)

            if is_callback:
                await message.edit_text(text, reply_markup=kb.as_markup(), parse_mode='HTML')
            else:
                await message.answer(text, reply_markup=kb.as_markup(), parse_mode='HTML')
            return

        kb = my_links_kb(links)
        text = "<b>Ваши анонимные ссылки:</b>\n\nВыберите ссылку для управления"

        if is_callback:
            await message.edit_text(text, reply_markup=kb.as_markup(), parse_mode='HTML')
        else:
            await message.answer(text, reply_markup=kb.as_markup(), parse_mode='HTML')


@router.callback_query(F.data.startswith("link_"))
async def link_details(callback: CallbackQuery):
    try:
        link_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        stmt = select(AskLink).where(AskLink.id == link_id, AskLink.owner_id == callback.from_user.id)
        result = await s.execute(stmt)
        link = result.scalar_one_or_none()

        if not link:
            await callback.answer("Ссылка не найдена или принадлежит другому пользователю", show_alert=True)
            return

        status = "Активна" if link.is_active else "Отключена"
        dest = "только в личку" if link.destination_type == "private" else "в канал/группу + в личку"
        reveal = "с раскрытием отправителя" if link.reveal_in_channel else "полностью анонимно"

        text = (
            f"<b>🔗 Ссылка:</b> {link.secret[:8]}...\n"
            f"<b>Статус:</b> {status}\n"
            f"<b>Куда приходят вопросы:</b> {dest}\n"
            f"<b>В канале:</b> {reveal}\n\n"
            f"<b>Что хотите сделать с этой ссылкой?</b>"
        )

        kb = link_actions_kb(link.id)
        await callback.message.edit_text(
            text,
            reply_markup=kb.as_markup(),
            parse_mode='HTML'
        )


@router.callback_query(F.data.startswith("deactivate_"))
async def deactivate(callback: CallbackQuery):
    try:
        link_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        stmt = select(AskLink).where(AskLink.id == link_id, AskLink.owner_id == callback.from_user.id)
        result = await s.execute(stmt)
        link = result.scalar_one_or_none()
        if link:
            link.is_active = False
            await s.commit()
            await callback.message.edit_text(
                "Ссылка успешно отключена.\nПо ней больше никто не сможет писать.",
                parse_mode='HTML'
            )
        else:
            await callback.answer("Ссылка не найдена", show_alert=True)


@router.callback_query(F.data.startswith("delete_"))
async def delete_link(callback: CallbackQuery):
    try:
        link_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка при удалении", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        stmt = delete(AskLink).where(
            AskLink.id == link_id,
            AskLink.owner_id == callback.from_user.id
        )
        result = await s.execute(stmt)
        await s.commit()

        if result.rowcount > 0:
            kb = InlineKeyboardBuilder()
            kb.button(text="Назад к списку", callback_data="my_links")

            await callback.message.edit_text(
                "Ссылка полностью удалена из системы.",
                reply_markup=kb.as_markup(),
                parse_mode='HTML'
            )
            await callback.answer("Удалено!")
        else:
            await callback.answer("Не удалось удалить — возможно, ссылка уже удалена", show_alert=True)