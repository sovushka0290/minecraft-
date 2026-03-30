from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_nickname = State()
    waiting_report_photo = State()
    waiting_report_amount = State()


class AdminStates(StatesGroup):
    # Создание задачи
    task_title = State()
    task_type = State()
    task_amount = State()
    task_deadline = State()
    task_assign = State()

    # Объявление
    announcement_text = State()

    # Варн
    warn_reason = State()

    # Склад
    warehouse_item = State()
    warehouse_qty = State()
