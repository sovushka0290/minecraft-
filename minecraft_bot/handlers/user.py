from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from states.states import UserStates, AdminStates
from services.user_service import get_or_create_user, update_nickname
from services.task_service import (
    get_user_tasks, get_task, save_report, progress_bar
)
from services.warehouse_service import get_warehouse
from keyboards.main_menu import main_menu_kb, back_to_main_kb, back_and_main_kb
from keyboards.tasks import tasks_list_kb, task_detail_kb, cancel_kb, report_amount_kb
from keyboards.admin import admin_menu_kb

router = Router()


# ── /start ──────────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(message.from_user.id)
    if user["nickname"].startswith("Player_"):
        await message.answer(
            "👋 Добро пожаловать!\n\nВведи свой <b>ник в Minecraft</b>:",
            parse_mode="HTML",
        )
        await state.set_state(UserStates.waiting_nickname)
        return
    await _show_main_menu(message, user)


@router.message(UserStates.waiting_nickname)
async def set_nickname(message: Message, state: FSMContext):
    nick = message.text.strip()
    if len(nick) < 3 or len(nick) > 24:
        await message.answer("❌ Ник должен быть от 3 до 24 символов. Попробуй снова:")
        return
    await update_nickname(message.from_user.id, nick)
    await state.clear()
    user = await get_or_create_user(message.from_user.id)
    await message.answer(f"✅ Ник установлен: <b>{nick}</b>", parse_mode="HTML")
    await _show_main_menu(message, user)


# ── Главное меню ─────────────────────────────────────────────────────────────
@router.callback_query(F.data == "main_menu")
async def cb_main_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(cb.from_user.id)
    kb = admin_menu_kb() if cb.from_user.id in ADMIN_IDS else main_menu_kb()
    text = (
        f"🏠 <b>Главное меню</b>\n\n"
        f"👤 {user['nickname']} | 🎖 {user['role']} | ⭐ {user['reputation']} реп."
    )
    await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cb.answer()


# ── Мои задачи ───────────────────────────────────────────────────────────────
@router.callback_query(F.data == "my_tasks")
async def cb_my_tasks(cb: CallbackQuery):
    tasks = await get_user_tasks(cb.from_user.id)
    if not tasks:
        await cb.message.edit_text(
            "📋 <b>Мои задачи</b>\n\nУ тебя пока нет активных задач.",
            reply_markup=back_to_main_kb(), parse_mode="HTML"
        )
        await cb.answer()
        return
    lines = ["📋 <b>Мои задачи</b>\n"]
    for t in tasks:
        bar = progress_bar(t["progress"], t["required_amount"])
        icon = "✅" if t["ut_status"] == "done" else "⏳"
        lines.append(f"{icon} <b>{t['title']}</b>\n   {bar}\n   🗓 {t['deadline'] or '—'}")
    await cb.message.edit_text(
        "\n".join(lines), reply_markup=tasks_list_kb(tasks), parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("task_detail:"))
async def cb_task_detail(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[1])
    task = await get_task(task_id)
    tasks = await get_user_tasks(cb.from_user.id)
    ut = next((t for t in tasks if t["id"] == task_id), None)
    if not task or not ut:
        await cb.answer("Задача не найдена.", show_alert=True)
        return
    bar = progress_bar(ut["progress"], task["required_amount"])
    status_map = {"active": "⏳ В работе", "done": "✅ Выполнено"}
    text = (
        f"📋 <b>{task['title']}</b>\n\n"
        f"📦 Тип: {task['task_type']}\n"
        f"📊 Прогресс: {bar}\n"
        f"   ({ut['progress']} / {task['required_amount']})\n"
        f"🗓 Дедлайн: {task['deadline'] or '—'}\n"
        f"🔖 Статус: {status_map.get(ut['ut_status'], ut['ut_status'])}"
    )
    await cb.message.edit_text(
        text,
        reply_markup=task_detail_kb(task_id, ut["ut_status"] == "done"),
        parse_mode="HTML"
    )
    await cb.answer()


# ── Отчёт ────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("submit_report:"))
async def cb_submit_report(cb: CallbackQuery, state: FSMContext):
    task_id = int(cb.data.split(":")[1])
    await state.set_state(UserStates.waiting_report_photo)
    await state.update_data(report_task_id=task_id)
    await cb.message.edit_text(
        "📸 Отправь <b>скриншот</b> как доказательство выполнения задачи:",
        reply_markup=cancel_kb(), parse_mode="HTML"
    )
    await cb.answer()


@router.message(UserStates.waiting_report_photo, F.photo)
async def receive_report_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data["report_task_id"]
    photo_id = message.photo[-1].file_id
    await state.update_data(report_photo_id=photo_id)
    await state.set_state(UserStates.waiting_report_amount)
    await message.answer(
        "📦 Сколько единиц ты выполнил? Выбери или введи вручную:",
        reply_markup=report_amount_kb(task_id)
    )


@router.callback_query(F.data.startswith("report_amount:"), UserStates.waiting_report_amount)
async def cb_report_amount(cb: CallbackQuery, state: FSMContext, bot=None):
    _, task_id_str, amount_str = cb.data.split(":")
    await _finalize_report(cb.message, cb.from_user.id, state,
                           int(task_id_str), int(amount_str), cb.bot)
    await cb.answer()


@router.message(UserStates.waiting_report_amount)
async def text_report_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи целое число больше 0:")
        return
    data = await state.get_data()
    await _finalize_report(message, message.from_user.id, state,
                           data["report_task_id"], amount, message.bot)


async def _finalize_report(msg, tg_id: int, state: FSMContext,
                            task_id: int, amount: int, bot):
    from config import ADMIN_IDS
    from keyboards.admin import report_review_kb
    data = await state.get_data()
    photo_id = data["report_photo_id"]
    report_id = await save_report(tg_id, task_id, photo_id, amount)
    await state.clear()
    user = await get_or_create_user(tg_id)
    task = await get_task(task_id)
    await msg.answer("✅ Отчёт отправлен на проверку!", reply_markup=back_to_main_kb())
    # Пересылаем всем админам
    admin_text = (
        f"📥 <b>Новый отчёт</b>\n\n"
        f"👤 Игрок: {user['nickname']}\n"
        f"📋 Задача: {task['title']}\n"
        f"📦 Количество: {amount}\n"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id, photo_id,
                caption=admin_text,
                reply_markup=report_review_kb(report_id),
                parse_mode="HTML"
            )
        except Exception:
            pass


# ── Профиль ──────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "profile")
async def cb_profile(cb: CallbackQuery):
    user = await get_or_create_user(cb.from_user.id)
    from services.user_service import get_user_warns
    warns = await get_user_warns(cb.from_user.id)
    tasks = await get_user_tasks(cb.from_user.id)
    done = sum(1 for t in tasks if t["ut_status"] == "done")
    text = (
        f"⚙️ <b>Профиль</b>\n\n"
        f"👤 Ник: <b>{user['nickname']}</b>\n"
        f"🎖 Роль: {user['role']}\n"
        f"⭐ Репутация: {user['reputation']}\n"
        f"📋 Задач выполнено: {done}\n"
        f"⚠️ Варнов: {warns}/3\n"
    )
    await cb.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await cb.answer()


# ── Склад ─────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "warehouse")
async def cb_warehouse(cb: CallbackQuery):
    items = await get_warehouse()
    if not items:
        text = "📦 <b>Склад</b>\n\nСклад пуст."
    else:
        lines = ["📦 <b>Склад</b>\n"]
        for item in items:
            lines.append(f"• {item['item_name']}: <b>{item['quantity']}</b> шт.")
        text = "\n".join(lines)
    await cb.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await cb.answer()


# ── Статистика ───────────────────────────────────────────────────────────────
@router.callback_query(F.data == "stats")
async def cb_stats(cb: CallbackQuery):
    from services.user_service import get_all_users
    users = await get_all_users()
    lines = ["📊 <b>Топ игроков по репутации</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(users[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{medal} {u['nickname']} — ⭐{u['reputation']}")
    await cb.message.edit_text(
        "\n".join(lines), reply_markup=back_to_main_kb(), parse_mode="HTML"
    )
    await cb.answer()
