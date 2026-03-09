from aiogram import Router, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, SuccessfulPayment, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import AsyncSessionLocal
from database.models import User
from config import PREMIUM_PRICE_STARS, PREMIUM_DAYS, PAYMENT_PROVIDER_TOKEN
from datetime import datetime, timedelta

router = Router()

# Цена теперь фиксирована 77 звёзд (можно оставить в config, но для примера переопределим здесь)
PREMIUM_PRICE_STARS = 77  # ← твоя новая цена


@router.callback_query(F.data == "buy_premium")
async def buy_premium(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user and user.is_premium and user.premium_expires and user.premium_expires > datetime.utcnow():
            expires = user.premium_expires.strftime("%d.%m.%Y в %H:%M")
            text = (
                "<b>💎 У вас уже активна премиум-подписка!</b>\n\n"
                f"Действует до: <b>{expires}</b>\n\n"
                "<b>Что даёт премиум:</b>\n"
                "• Видите username или ID автора каждого вопроса\n"
                "• Полная анонимность для тех, кто пишет вам\n"
                "• Поддержка проекта и будущие эксклюзивные функции\n\n"
                "Спасибо, что вы с нами! ✨"
            )
            kb = InlineKeyboardBuilder()
            kb.button(text="← Вернуться в меню", callback_data="back_to_main")
            kb.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
            await callback.answer()
            return

    # Если подписки нет или истекла — показываем инвойс
    prices = [LabeledPrice(label="Премиум на 30 дней", amount=PREMIUM_PRICE_STARS)]

    await callback.message.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="💎 Премиум-подписка",
        description=(
            "Получите расширенные возможности:\n"
            "• Видите username или ID автора каждого вопроса\n"
            "• Полная анонимность для пишущих вам людей\n"
            "• Поддержка проекта и будущие эксклюзивные функции"
        ),
        payload="premium_subscription",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )
    await callback.answer("Открываем оплату...")


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username
            )
            session.add(user)

        user.is_premium = True
        user.premium_expires = datetime.utcnow() + timedelta(days=PREMIUM_DAYS)
        await session.commit()

        expires = user.premium_expires.strftime("%d.%m.%Y в %H:%M")

    await message.answer(
        "<b>🎉 Премиум-подписка успешно активирована!</b>\n\n"
        f"Действует до: <b>{expires}</b>\n\n"
        "<b>Теперь вы получаете:</b>\n"
        "• Username или ID автора каждого вопроса\n"
        "• Полная анонимность для тех, кто пишет вам\n"
        "• Поддержка проекта и будущие крутые фичи\n\n"
        "Спасибо огромное! ✨"
    )