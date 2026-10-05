from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

import database as db
from config import config

router = Router(name="common")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    db.upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "👋 Hi! I collect project requests for a Python developer.\n\n"
        "/order — create a new request\n"
        "/my — your requests and their status\n"
        "/help — how this works\n"
        "/cancel — cancel whatever you're doing",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "This bot collects project requests (website, Telegram bot, automation, scraper).\n\n"
        "Send /order, answer a few quick questions, and the request is saved and forwarded "
        "to the developer. Use /my to check the status of your requests at any time."
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Nothing to cancel right now.")
        return
    await state.clear()
    await message.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())


@router.message(Command("whoami"))
async def whoami(message: Message) -> None:
    role = "admin" if message.from_user.id in config.ADMIN_IDS else "user"
    await message.answer(f"Your Telegram ID: `{message.from_user.id}`\nRole: {role}", parse_mode="Markdown")
