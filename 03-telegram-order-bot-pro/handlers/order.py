"""The /order conversation: service -> budget -> deadline -> description -> confirm."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import keyboards as kb
from config import config
from states import OrderForm

router = Router(name="order")


@router.message(Command("order"))
async def order_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(OrderForm.service)
    await message.answer("What do you need?", reply_markup=kb.services_kb())


@router.callback_query(OrderForm.service, F.data.startswith("service:"))
async def choose_service(call: CallbackQuery, state: FSMContext) -> None:
    service = call.data.split(":", 1)[1]
    await state.update_data(service=service, service_label=db.SERVICES[service])
    await state.set_state(OrderForm.budget)
    await call.message.edit_text(
        f"Service: {db.SERVICES[service]}\n\nWhat's your budget?", reply_markup=kb.budgets_kb()
    )
    await call.answer()


@router.callback_query(OrderForm.budget, F.data == "budget:custom")
async def budget_custom(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OrderForm.budget_custom)
    await call.message.edit_text("Please type your budget as a number (USD), e.g. 220")
    await call.answer()


@router.message(OrderForm.budget_custom, F.text.regexp(r"^\d{1,6}$"))
async def budget_custom_value(message: Message, state: FSMContext) -> None:
    await state.update_data(budget=f"${message.text}")
    await state.set_state(OrderForm.deadline)
    await message.answer("When do you need it by?", reply_markup=kb.deadlines_kb())


@router.message(OrderForm.budget_custom)
async def budget_custom_invalid(message: Message) -> None:
    await message.answer("Please send a whole number, for example 220.")


@router.callback_query(OrderForm.budget, F.data.startswith("budget:"))
async def choose_budget(call: CallbackQuery, state: FSMContext) -> None:
    key = call.data.split(":", 1)[1]
    await state.update_data(budget=db.BUDGETS[key])
    await state.set_state(OrderForm.deadline)
    await call.message.edit_text("When do you need it by?", reply_markup=kb.deadlines_kb())
    await call.answer()


@router.callback_query(OrderForm.deadline, F.data.startswith("deadline:"))
async def choose_deadline(call: CallbackQuery, state: FSMContext) -> None:
    key = call.data.split(":", 1)[1]
    await state.update_data(deadline=db.DEADLINES[key])
    await state.set_state(OrderForm.description)
    await call.message.edit_text("Last step — briefly describe what you need (a few sentences is enough):")
    await call.answer()


@router.message(OrderForm.description, F.text)
async def get_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()[:1500]
    await state.update_data(description=description)
    data = await state.get_data()
    summary = (
        "Please confirm your request:\n\n"
        f"🛠 Service: {data['service_label']}\n"
        f"💰 Budget: {data['budget']}\n"
        f"⏱ Deadline: {data['deadline']}\n"
        f"📝 Description: {description}"
    )
    await state.set_state(OrderForm.confirm)
    await message.answer(summary, reply_markup=kb.confirm_kb())


@router.callback_query(OrderForm.confirm, F.data == "confirm:no")
async def restart_order(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OrderForm.service)
    await call.message.edit_text("No problem, let's start over. What do you need?", reply_markup=kb.services_kb())
    await call.answer()


@router.callback_query(OrderForm.confirm, F.data == "confirm:yes")
async def submit_order(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = db.add_order(
        user_id=call.from_user.id,
        username=call.from_user.username,
        service=data["service"],
        budget=data["budget"],
        deadline=data["deadline"],
        description=data["description"],
    )
    await state.clear()
    await call.message.edit_text(f"✅ Request #{order_id} saved! I'll get back to you shortly.")
    await call.answer("Sent!")

    for admin_id in config.ADMIN_IDS:
        try:
            await call.bot.send_message(
                admin_id,
                f"🆕 New request #{order_id}\n"
                f"From: @{call.from_user.username or call.from_user.id}\n"
                f"Service: {data['service_label']}\n"
                f"Budget: {data['budget']}\n"
                f"Deadline: {data['deadline']}\n"
                f"Description: {data['description']}",
                reply_markup=kb.order_status_kb(db.get_order(order_id)),
            )
        except Exception:
            pass  # admin may have blocked the bot; don't crash the flow for the user


@router.message(Command("my"))
async def my_orders(message: Message) -> None:
    orders = db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("You have no requests yet. Use /order to create one.")
        return
    for o in orders:
        text = (
            f"#{o.id} — {db.STATUSES[o.status]}\n"
            f"{db.SERVICES.get(o.service, o.service)}, {o.budget}, {o.deadline}\n"
            f"{o.created_at}"
        )
        markup = kb.cancel_order_kb(o.id) if o.status == "new" else None
        await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("usercancel:"))
async def user_cancel_order(call: CallbackQuery) -> None:
    order_id = int(call.data.split(":")[1])
    order = db.get_order(order_id)
    if order is None or order.user_id != call.from_user.id:
        await call.answer("Not found.", show_alert=True)
        return
    if order.status != "new":
        await call.answer("This request is already being handled.", show_alert=True)
        return
    db.update_status(order_id, "cancelled")
    await call.message.edit_text(f"#{order_id} — ❌ Cancelled")
    await call.answer("Cancelled")
