from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from states.states import AdminStates
from services.task_service import (
    get_active_tasks, create_task, delete_task,
    get_report, accept_report, reject_report
)
from services.user_service import get_all_users, add_warn
from services.warehouse_service import get_warehouse, set_warehouse_item
from keyboards.admin import (
    admin_menu_kb, admin_tasks_kb, task_type_kb, assign_kb,
    players_kb, confirm_kick_kb
)
from keyboards.main_menu import back_to_main_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── Guard ─────────────────────────────────────────────────────────────────────
async def admin_only(cb: CallbackQuery) -> bool:
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔ Нет доступа.", show_alert=True)
        return False
    return True


# ── Команда /admin ─────────────────────────────────────────────────────────────
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛡 <b>Админ-панель</b>", reply_markup=admin_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(cb: CallbackQuery, state: FSMContext):
    if not await admin_only(cb):
        return
    await state.clear()
    await cb.message.edit_text("🛡 <b>Админ-панель</b>", reply_markup=admin_menu_kb(), parse_mode="HTML")
    await cb.answer()


# ── Объявление ────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_announce")
async def cb_admin_announce(cb: CallbackQuery, state: FSMContext):
    if not await admin_only(cb):
        return
    await state.set_state(AdminStates.announcement_text)
    await cb.message.edit_text("📢 Введи текст объявления:")
    await cb.answer()


@router.message(AdminStates.announcement_text)
async def send_announcement(message: Message, state: FSMContext, bot: Bot):
    text = f"📢 <b>Объявление</b>\n\n{message.text}"
    users = await get_all_users()
    sent = 0
    for u in users:
        try:
            await bot.send_message(u["telegram_id"], text, parse_mode="HTML")
            sent += 1
        except Exception:
            pass
    await state.clear()
    await message.answer(
        f"✅ Объявление отправлено {sent} игрокам.",
        reply_markup=admin_menu_kb()
    )


# ── Управление задачами ───────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_tasks")
async def cb_admin_tasks(cb: CallbackQuery):
    if not await admin_only(cb):
        return
    tasks = await get_active_tasks()
    text = "📋 <b>Активные задачи</b>\n\nНажми на задачу, чтобы удалить её."
    await cb.message.edit_text(text, reply_markup=admin_tasks_kb(tasks), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data.startswith("admin_delete_task:"))
async def cb_delete_task(cb: CallbackQuery):
    if not await admin_only(cb):
        return
    task_id = int(cb.data.split(":")[1])
    await delete_task(task_id)
    await cb.answer("🗑 Задача удалена.", show_alert=True)
    tasks = await get_active_tasks()
    await cb.message.edit_reply_markup(reply_markup=admin_tasks_kb(tasks))


@router.callback_query(F.data == "admin_create_task")
async def cb_create_task_start(cb: CallbackQuery, state: FSMContext):
    if not await admin_only(cb):
        return
    await state.set_state(AdminStates.task_title)
    await cb.message.edit_text("📝 Введи <b>название задачи</b>:", parse_mode="HTML")
    await cb.answer()


@router.message(AdminStates.task_title)
async def task_set_title(message: Message, state: FSMContext):
    await state.update_data(task_title=message.text.strip())
    await state.set_state(AdminStates.task_type)
    await message.answer("📦 Выбери <b>тип задачи</b>:", reply_markup=task_type_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("task_type_select:"), AdminStates.task_type)
async def task_set_type(cb: CallbackQuery, state: FSMContext):
    task_type = cb.data.split(":")[1]
    await state.update_data(task_type=task_type)
    await state.set_state(AdminStates.task_amount)
    await cb.message.edit_text(f"🔢 Тип: <b>{task_type}</b>\n\nВведи <b>необходимое количество</b>:", parse_mode="HTML")
    await cb.answer()


@router.message(AdminStates.task_amount)
async def task_set_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи целое число больше 0:")
        return
    await state.update_data(task_amount=amount)
    await state.set_state(AdminStates.task_deadline)
    await message.answer("🗓 Введи <b>дедлайн</b> (формат: ГГГГ-ММ-ДД):", parse_mode="HTML")


@router.message(AdminStates.task_deadline)
async def task_set_deadline(message: Message, state: FSMContext):
    deadline = message.text.strip()
    await state.update_data(task_deadline=deadline)
    await state.set_state(AdminStates.task_assign)
    await message.answer("👥 Кому назначить задачу?", reply_markup=assign_kb())


@router.callback_query(F.data.startswith("assign:"), AdminStates.task_assign)
async def task_set_assign(cb: CallbackQuery, state: FSMContext, bot: Bot):
    assign_type = cb.data.split(":")[1]
    if assign_type == "specific":
        await cb.message.edit_text(
            "✏️ Введи Telegram ID игроков через запятую (пример: 123456,789012):"
        )
        await cb.answer()
        return

    data = await state.get_data()
    task_id = await create_task(
        data["task_title"], data["task_type"],
        data["task_amount"], data["task_deadline"], "all"
    )
    await state.clear()

    # Уведомить всех игроков
    users = await get_all_users()
    for u in users:
        try:
            await bot.send_message(
                u["telegram_id"],
                f"📋 <b>Новая задача!</b>\n\n"
                f"<b>{data['task_title']}</b>\n"
                f"📦 {data['task_type']} × {data['task_amount']}\n"
                f"🗓 До: {data['task_deadline']}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await cb.message.edit_text(
        f"✅ Задача <b>#{task_id}</b> создана и назначена всем игрокам!",
        reply_markup=admin_menu_kb(), parse_mode="HTML"
    )
    await cb.answer()


@router.message(AdminStates.task_assign)
async def task_assign_specific(message: Message, state: FSMContext, bot: Bot):
    ids_str = message.text.strip()
    data = await state.get_data()
    task_id = await create_task(
        data["task_title"], data["task_type"],
        data["task_amount"], data["task_deadline"], ids_str
    )
    await state.clear()
    await message.answer(
        f"✅ Задача <b>#{task_id}</b> создана и назначена указанным игрокам!",
        reply_markup=admin_menu_kb(), parse_mode="HTML"
    )


# ── Проверка отчётов ──────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("report_accept:"))
async def cb_accept_report(cb: CallbackQuery, bot: Bot):
    if not await admin_only(cb):
        return
    report_id = int(cb.data.split(":")[1])
    report = await get_report(report_id)
    if not report:
        await cb.answer("Отчёт не найден.", show_alert=True)
        return
    await accept_report(report_id)
    await cb.message.edit_caption(
        caption=f"✅ <b>Отчёт принят</b>\n\n👤 {report['nickname']}\n📋 {report['title']}",
        parse_mode="HTML"
    )
    await bot.send_message(
        report["telegram_id"],
        f"✅ Твой отчёт по задаче <b>{report['title']}</b> принят!\n⭐ +5 репутации",
        parse_mode="HTML"
    )
    await cb.answer("✅ Принято!")


@router.callback_query(F.data.startswith("report_reject:"))
async def cb_reject_report(cb: CallbackQuery, bot: Bot):
    if not await admin_only(cb):
        return
    report_id = int(cb.data.split(":")[1])
    report = await get_report(report_id)
    if not report:
        await cb.answer("Отчёт не найден.", show_alert=True)
        return
    await reject_report(report_id)
    await cb.message.edit_caption(
        caption=f"❌ <b>Отчёт отклонён</b>\n\n👤 {report['nickname']}\n📋 {report['title']}",
        parse_mode="HTML"
    )
    await bot.send_message(
        report["telegram_id"],
        f"❌ Твой отчёт по задаче <b>{report['title']}</b> был отклонён.\nОбратись к администратору.",
        parse_mode="HTML"
    )
    await cb.answer("❌ Отклонено.")


# ── Игроки и варны ────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_players")
async def cb_admin_players(cb: CallbackQuery):
    if not await admin_only(cb):
        return
    users = await get_all_users()
    await cb.message.edit_text(
        "👥 <b>Список игроков</b>\n\nНажми на игрока, чтобы выдать варн:",
        reply_markup=players_kb(users), parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data == "admin_warns")
async def cb_admin_warns(cb: CallbackQuery):
    if not await admin_only(cb):
        return
    await cb.message.edit_text(
        "⚖️ <b>Выдать варн</b>\n\nВыбери игрока:",
        reply_markup=players_kb(await get_all_users()), parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin_warn_player:"))
async def cb_warn_player_start(cb: CallbackQuery, state: FSMContext):
    if not await admin_only(cb):
        return
    target_id = int(cb.data.split(":")[1])
    await state.update_data(warn_target_id=target_id)
    await state.set_state(AdminStates.warn_reason)
    await cb.message.edit_text(
        f"✏️ Введи <b>причину варна</b> для игрока {target_id}:", parse_mode="HTML"
    )
    await cb.answer()


@router.message(AdminStates.warn_reason)
async def give_warn(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_id = data["warn_target_id"]
    reason = message.text.strip()
    warn_count = await add_warn(target_id, reason)
    await state.clear()

    await bot.send_message(
        target_id,
        f"⚠️ <b>Тебе выдан варн</b>\n\nПричина: {reason}\n"
        f"Всего варнов: {warn_count}/3",
        parse_mode="HTML"
    )

    if warn_count >= 3:
        await message.answer(
            f"⚠️ У игрока {target_id} уже {warn_count} варна!\n"
            f"Рекомендуется кик.",
            reply_markup=confirm_kick_kb(target_id)
        )
    else:
        await message.answer(
            f"✅ Варн выдан. Итого у игрока: {warn_count}/3",
            reply_markup=admin_menu_kb()
        )


@router.callback_query(F.data.startswith("kick_confirm:"))
async def cb_kick(cb: CallbackQuery, bot: Bot):
    if not await admin_only(cb):
        return
    target_id = int(cb.data.split(":")[1])
    try:
        await bot.send_message(
            target_id,
            "🔨 <b>Ты исключён из сервера</b>.\n\nОбратись к главному администратору.",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await cb.message.edit_text(
        f"🔨 Игрок {target_id} уведомлён о кике.",
        reply_markup=admin_menu_kb()
    )
    await cb.answer("Игрок уведомлён.")


# ── Склад (admin) ─────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_warehouse")
async def cb_admin_warehouse(cb: CallbackQuery, state: FSMContext):
    if not await admin_only(cb):
        return
    items = await get_warehouse()
    lines = ["📦 <b>Склад</b> (управление)\n"]
    for item in items:
        lines.append(f"• {item['item_name']}: {item['quantity']}")
    lines.append("\nВведи в формате: <b>название количество</b>\nПример: Дерево 100")
    await cb.message.edit_text("\n".join(lines), parse_mode="HTML")
    await state.set_state(AdminStates.warehouse_item)
    await cb.answer()


@router.message(AdminStates.warehouse_item)
async def admin_set_warehouse(message: Message, state: FSMContext):
    parts = message.text.strip().rsplit(" ", 1)
    if len(parts) != 2:
        await message.answer("❌ Формат: название количество")
        return
    item_name, qty_str = parts
    try:
        qty = int(qty_str)
    except ValueError:
        await message.answer("❌ Количество должно быть числом.")
        return
    await set_warehouse_item(item_name.strip(), qty)
    await state.clear()
    await message.answer(
        f"✅ Склад обновлён: {item_name} = {qty}",
        reply_markup=admin_menu_kb()
    )
