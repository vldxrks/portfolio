"""Admin-only panel: order list with pagination & status changes, stats, broadcast, CSV export."""
import os

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import database as db
import keyboards as kb
from config import config
from states import AdminForm

router = Router(name="admin")
router.message.filter(F.from_user.id.in_(config.ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(config.ADMIN_IDS))


@router.message(Command("admin"))
async def admin_menu(message: Message) -> None:
    await message.answer("Admin panel:", reply_markup=kb.admin_menu_kb())


@router.callback_query(F.data == "admin:menu")
async def back_to_menu(call: CallbackQuery) -> None:
    await call.message.edit_text("Admin panel:", reply_markup=kb.admin_menu_kb())
    await call.answer()


@router.callback_query(F.data.startswith("admin:list:"))
async def list_orders(call: CallbackQuery) -> None:
    _, _, status_filter, page_str = call.data.split(":")
    page = int(page_str)
    status = None if status_filter == "all" else status_filter
    orders, total = db.get_orders_page(status, page)
    if not orders:
        await call.message.edit_text("No orders here yet.", reply_markup=kb.admin_menu_kb())
        await call.answer()
        return
    await call.message.edit_text(
        f"Orders ({status_filter}) — {total} total:", reply_markup=kb.orders_list_kb(orders, status_filter, page, total)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:view:"))
async def view_order(call: CallbackQuery) -> None:
    _, _, order_id_str, status_filter, page = call.data.split(":")
    order = db.get_order(int(order_id_str))
    if order is None:
        await call.answer("Not found.", show_alert=True)
        return
    text = (
        f"#{order.id} — {db.STATUSES[order.status]}\n"
        f"User: @{order.username or order.user_id}\n"
        f"Service: {db.SERVICES.get(order.service, order.service)}\n"
        f"Budget: {order.budget}\n"
        f"Deadline: {order.deadline}\n"
        f"Description: {order.description}\n"
        f"Created: {order.created_at}"
    )
    await call.message.edit_text(text, reply_markup=kb.order_status_kb(order))
    await call.answer()


@router.callback_query(F.data.startswith("setstatus:"))
async def set_status(call: CallbackQuery) -> None:
    _, order_id_str, status = call.data.split(":")
    order_id = int(order_id_str)
    db.update_status(order_id, status)
    order = db.get_order(order_id)
    await call.message.edit_text(
        f"#{order.id} status updated to {db.STATUSES[status]}", reply_markup=kb.order_status_kb(order)
    )
    await call.answer("Updated")
    try:
        await call.bot.send_message(
            order.user_id, f"Your request #{order.id} status changed: {db.STATUSES[status]}"
        )
    except Exception:
        pass


@router.callback_query(F.data == "admin:stats")
async def stats(call: CallbackQuery) -> None:
    s = db.get_stats()
    by_status = "\n".join(f"  {db.STATUSES.get(k, k)}: {v}" for k, v in s["by_status"].items()) or "  —"
    by_service = "\n".join(f"  {db.SERVICES.get(k, k)}: {v}" for k, v in s["by_service"]) or "  —"
    text = (
        f"📊 Stats\n\n"
        f"Total orders: {s['total_orders']}\n"
        f"Total users: {s['total_users']}\n"
        f"New today: {s['today_orders']}\n\n"
        f"By status:\n{by_status}\n\n"
        f"By service:\n{by_service}"
    )
    await call.message.edit_text(text, reply_markup=kb.admin_menu_kb())
    await call.answer()


@router.callback_query(F.data == "admin:export")
async def export_csv(call: CallbackQuery) -> None:
    path = "orders_export.csv"
    count = db.export_orders_csv(path)
    with open(path, "rb") as f:
        await call.message.answer_document(BufferedInputFile(f.read(), filename=path), caption=f"{count} orders")
    os.remove(path)
    await call.answer()


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminForm.broadcast_text)
    await call.message.edit_text("Send the message you want to broadcast to all users (or /cancel):")
    await call.answer()


@router.message(AdminForm.broadcast_text, F.text)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await state.set_state(AdminForm.broadcast_confirm)
    user_count = len(db.all_user_ids())
    await message.answer(
        f"Preview — will be sent to {user_count} users:\n\n{message.text}", reply_markup=kb.broadcast_confirm_kb()
    )


@router.callback_query(AdminForm.broadcast_confirm, F.data == "broadcast:cancel")
async def broadcast_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("Broadcast cancelled.", reply_markup=kb.admin_menu_kb())
    await call.answer()


@router.callback_query(AdminForm.broadcast_confirm, F.data == "broadcast:send")
async def broadcast_send(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    text = data["text"]
    await state.clear()
    sent, failed = 0, 0
    for user_id in db.all_user_ids():
        try:
            await call.bot.send_message(user_id, text)
            sent += 1
        except Exception:
            failed += 1
    await call.message.edit_text(f"Broadcast done. Sent: {sent}, failed: {failed}", reply_markup=kb.admin_menu_kb())
    await call.answer()
