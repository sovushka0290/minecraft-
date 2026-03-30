from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def tasks_list_kb(tasks: list) -> InlineKeyboardMarkup:
    rows = []
    for t in tasks:
        status_icon = "✅" if t["ut_status"] == "done" else "⏳"
        rows.append([InlineKeyboardButton(
            text=f"{status_icon} {t['title']}",
            callback_data=f"task_detail:{t['id']}"
        )])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_detail_kb(task_id: int, is_done: bool) -> InlineKeyboardMarkup:
    rows = []
    if not is_done:
        rows.append([InlineKeyboardButton(
            text="📤 Сдать отчёт",
            callback_data=f"submit_report:{task_id}"
        )])
    rows.append([
        InlineKeyboardButton(text="⬅️ Назад",    callback_data="my_tasks"),
        InlineKeyboardButton(text="🏠 Меню",     callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")],
    ])


def report_amount_kb(task_id: int) -> InlineKeyboardMarkup:
    quick = [1, 5, 10, 32, 64]
    rows = [[
        InlineKeyboardButton(text=str(q), callback_data=f"report_amount:{task_id}:{q}")
        for q in quick
    ]]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
