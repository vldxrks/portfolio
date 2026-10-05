# Telegram Order Bot — Pro

An upgraded version of the order-collection bot: inline-keyboard conversation,
a full admin panel, broadcasts, stats, CSV export and basic anti-spam.

## What's new compared to the basic version
- **Inline keyboards** instead of a reply keyboard — cleaner UX, buttons edit in place
- **Richer order form**: service, budget (presets + custom amount), deadline, free-text description, a confirmation step before saving
- **Order statuses**: 🆕 New → ⏳ In progress → ✅ Done / ❌ Cancelled, changeable by admins with one tap; the client is notified automatically on every status change
- **Admin panel** (`/admin`, restricted to `ADMIN_IDS`): paginated order list filtered by status, per-order detail view, stats screen, CSV export, broadcast to every known user
- **`/my`**: a client can see their own requests and cancel a pending one
- **Multiple admins**: `ADMIN_IDS` is a comma-separated list, not a single ID
- **Anti-spam middleware**: drops messages/clicks sent faster than `THROTTLE_SECONDS` apart per user
- **Logging** to a rotating file (`bot.log`) plus console
- **Tests** for the whole data layer (pytest), independent of Telegram

## Project structure
```
bot.py            entry point — wiring, logging, polling
config.py         reads and validates .env
database.py       SQLite layer: users, orders, stats, CSV export
states.py         FSM states for the order form and the broadcast flow
keyboards.py      all inline keyboards
middlewares.py    anti-spam throttling
handlers/
  common.py       /start, /help, /cancel, /whoami
  order.py        the order conversation + /my
  admin.py        admin panel: list, view, status change, stats, export, broadcast
tests/
  test_database.py
```

## Run
```bash
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```
Fill `.env`:
```
BOT_TOKEN=token from @BotFather
ADMIN_IDS=123456789,987654321   # your Telegram ID(s), from @userinfobot
```
Then:
```bash
python bot.py
```

## Test
```bash
pytest -q
```

## Commands
| Command | Who | Description |
|---|---|---|
| /start | everyone | greeting, registers the user |
| /order | everyone | start a new request |
| /my | everyone | your requests + cancel a pending one |
| /cancel | everyone | abort whatever you're doing |
| /whoami | everyone | shows your Telegram ID and role |
| /admin | admins only | open the admin panel |

## Notes for clients adapting this
- Add/remove services in `database.py` → `SERVICES`
- Add payment collection by inserting one more FSM state before `confirm`
- Swap SQLite for PostgreSQL by replacing `database.py`'s connection helper — the rest of the code doesn't change
- `ADMIN_IDS` supports several admins out of the box, useful for a small team
