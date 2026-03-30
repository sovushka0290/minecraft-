from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои задачи", callback_data="my_tasks")],
        [InlineKeyboardButton(text="📦 Склад",       callback_data="warehouse"),
         InlineKeyboardButton(text="📊 Статистика",  callback_data="stats")],
        [InlineKeyboardButton(text="⚙️ Профиль",     callback_data="profile")],
    ])


def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])


def back_and_main_kb(back_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb),
         InlineKeyboardButton(text="🏠 Меню",  callback_data="main_menu")],
    ])
