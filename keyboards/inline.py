# keyboards/inline.py

from aiogram.utils.keyboard import InlineKeyboardBuilder


def destination_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✉️ Только в личные сообщения мне", callback_data="dest_private")
    kb.button(text="📢 В канал/группу + мне в личку", callback_data="dest_channel_both")
    kb.adjust(1)
    return kb


def reveal_in_channel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Да, показывать кто написал (ник/ID)", callback_data="reveal_yes")
    kb.button(text="Нет, полная анонимность в канале", callback_data="reveal_no")
    kb.button(text="← Назад", callback_data="back_to_main")
    kb.adjust(1)
    return kb


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Создать ссылку", callback_data="confirm_create")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.button(text="← Назад", callback_data="back_to_main")
    kb.adjust(1)
    return kb


def my_links_kb(links):
    kb = InlineKeyboardBuilder()
    for link in links:
        status = "🟢 Активна" if link.is_active else "🔴 Отключена"
        kb.button(
            text=f"🔗 {link.secret[:8]}... ({status})",
            callback_data=f"link_{link.id}"
        )
    kb.button(text="✨ Создать новую ссылку", callback_data="create_link")
    kb.button(text="💎 Премиум / управление подпиской", callback_data="buy_premium")
    kb.button(text="← В главное меню", callback_data="back_to_main")
    kb.adjust(1)
    return kb


def link_actions_kb(link_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛑 Отключить ссылку", callback_data=f"deactivate_{link_id}")
    kb.button(text="🗑️ Удалить навсегда", callback_data=f"delete_{link_id}")
    kb.button(text="← Назад к списку ссылок", callback_data="my_links")
    kb.adjust(1)
    return kb


def question_actions_kb(message_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Ответить анонимно", callback_data=f"reply_{message_id}")
    kb.button(text="← В главное меню", callback_data="back_to_main")
    kb.adjust(1)
    return kb


def back_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="← Назад", callback_data="back_to_main")
    kb.adjust(1)
    return kb