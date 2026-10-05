from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    service = State()
    budget = State()
    budget_custom = State()
    deadline = State()
    description = State()
    confirm = State()


class AdminForm(StatesGroup):
    broadcast_text = State()
    broadcast_confirm = State()
