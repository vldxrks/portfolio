"""All inline keyboards in one place, built with InlineKeyboardBuilder."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import BUDGETS, DEADLINES, SERVICES, STATUSES, Order

PAGE_SIZE = 5


def services_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in SERVICES.items():
        b.button(text=label, callback_data=f"service:{key}")
    b.adjust(2)
    return b.as_markup()


def budgets_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in BUDGETS.items():
        b.button(text=label, callback_data=f"budget:{key}")
    b.button(text="💬 Custom amount", callback_data="budget:custom")
    b.adjust(2)
    return b.as_markup()


def deadlines_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in DEADLINES.items():
        b.button(text=label, callback_data=f"deadline:{key}")
    b.adjust(1)
    return b.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Submit", callback_data="confirm:yes")
    b.button(text="✏️ Start over", callback_data="confirm:no")
    b.adjust(2)
    return b.as_markup()


def cancel_order_kb(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Cancel this request", callback_data=f"usercancel:{order_id}")
    return b.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🆕 New orders", callback_data="admin:list:new:0")
    b.button(text="📋 All orders", callback_data="admin:list:all:0")
    b.button(text="📊 Stats", callback_data="admin:stats")
    b.button(text="📢 Broadcast", callback_data="admin:broadcast")
    b.button(text="📁 Export CSV", callback_data="admin:export")
    b.adjust(2, 2, 1)
    return b.as_markup()


def order_status_kb(order: Order) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in STATUSES.items():
        if key != order.status:
            b.button(text=label, callback_data=f"setstatus:{order.id}:{key}")
    b.adjust(1)
    return b.as_markup()


def orders_list_kb(orders: list[Order], status_filter: str, page: int, total: int) -> InlineKeyboardMarkup:
    from aiogram.types import InlineKeyboardButton

    rows: list[list[InlineKeyboardButton]] = []
    for o in orders:
        label = f"#{o.id} {STATUSES[o.status].split()[0]} {SERVICES.get(o.service, o.service)} — {o.budget}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"admin:view:{o.id}:{status_filter}:{page}")])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin:list:{status_filter}:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin:list:{status_filter}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="⬅️ Back to menu", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📤 Send to everyone", callback_data="broadcast:send")
    b.button(text="🚫 Cancel", callback_data="broadcast:cancel")
    b.adjust(1)
    return b.as_markup()
