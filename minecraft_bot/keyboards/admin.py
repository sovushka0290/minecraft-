from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Объявление",         callback_data="admin_announce")],
        [InlineKeyboardButton(text="📋 Управление задачами", callback_data="admin_tasks")],
        [InlineKeyboardButton(text="👥 Игроки",             callback_data="admin_players")],
        [InlineKeyboardButton(text="⚖️ Варны",              callback_data="admin_warns")],
        [InlineKeyboardButton(text="📦 Склад",              callback_data="admin_warehouse")],
        [InlineKeyboardButton(text="🏠 Главное меню",        callback_data="main_menu")],
    ])


def admin_tasks_kb(tasks: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"🗑 {t['title']}",
        callback_data=f"admin_delete_task:{t['id']}"
    )] for t in tasks]
    rows.append([InlineKeyboardButton(text="➕ Создать задачу", callback_data="admin_create_task")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_type_kb() -> InlineKeyboardMarkup:
    types = ["Сбор", "Строительство", "Добыча", "Крафт", "Охота"]
    rows = [[InlineKeyboardButton(text=t, callback_data=f"task_type_select:{t}")] for t in types]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def assign_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Всем игрокам",     callback_data="assign:all")],
        [InlineKeyboardButton(text="✏️ Конкретным (ID)",  callback_data="assign:specific")],
        [InlineKeyboardButton(text="❌ Отмена",            callback_data="admin_menu")],
    ])


def report_review_kb(report_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять",  callback_data=f"report_accept:{report_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"report_reject:{report_id}"),
        ]
    ])


def players_kb(users: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"⚖️ {u['nickname']} (ID: {u['telegram_id']})",
        callback_data=f"admin_warn_player:{u['telegram_id']}"
    )] for u in users]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kick_kb(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔨 Кикнуть", callback_data=f"kick_confirm:{telegram_id}"),
            InlineKeyboardButton(text="⬅️ Отмена",  callback_data="admin_menu"),
        ]
    ])
