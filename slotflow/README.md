# SlotFlow

**Meeting-room booking service with a temporary slot hold.** Pick a room, choose a time slot, hold it for 15 minutes, then confirm or let it expire. Includes a customer-facing catalog and an admin dashboard.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/Vanilla_JS-no_build-F7DF1E?logo=javascript&logoColor=black)

<!-- Add your own screenshots to docs/screenshots/ and uncomment:
![Catalog](docs/screenshots/catalog.png)
![Admin dashboard](docs/screenshots/admin.png)
-->

## Features

**For customers**
- Room catalog with search, floor filter, capacity filter and equipment filter
- Chrono-grid slot picker for today, tomorrow and the day after (busy and past slots are disabled)
- Temporary **hold** with a live countdown, then **Confirm** or let it expire automatically
- "My Bookings" with cancellation (free up to 30 minutes before the start)
- Registration, sign-in and sign-out (session cookies, hashed passwords)
- Responsive layout (desktop and mobile)

**For administrators** (`/admin`)
- KPI cards: total bookings, active holds (and how many expire in under 5 minutes), current room occupancy
- Timeline grid 08:00–22:00 per room (confirmed / on hold)
- Bookings feed with status filters and search by code, name, e-mail or room
- Role-based access: non-admins are redirected, admin API returns `403`

**Backend guarantees**
- Double booking is impossible: a **partial unique index** in the database allows only one `pending`/`confirmed` booking per room, day and slot
- Expired holds are released lazily on every request, no background worker needed
- Server-side validation of days, slots, ownership and cancellation window

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask 3.0 |
| Database | SQLite (standard library `sqlite3`) |
| Auth | Flask sessions, Werkzeug password hashing |
| Frontend | HTML, CSS, vanilla JavaScript (no build step, no npm) |
| Fonts | Manrope, JetBrains Mono (Google Fonts) |

## Project structure

```
slotflow/
├── app.py              # Flask app: API, auth, admin, DB schema, seed data, CLI commands
├── smoke_test.py       # End-to-end test of the main scenarios
├── requirements.txt    # Pinned Python dependencies
├── .env.example        # Configuration template (no secrets)
└── static/
    ├── index.html      # Customer site
    ├── admin.html      # Admin dashboard
    ├── style.css
    ├── app.js          # Customer-site logic
    └── img/            # Photos
```

## Quick start

Requires **Python 3.10+**.

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>/slotflow            # the folder that contains app.py

python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env               # then edit SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
set -a && source .env && set +a    # load the variables into the current shell
flask --app app init-db            # creates slotflow.db, seeds 4 rooms and the admin user
PORT=5001 python app.py            # open http://127.0.0.1:5001
```

> **macOS:** port 5000 is used by the AirPlay Receiver and answers `403`, so the examples use port `5001`.
> **Windows:** variables from `.env` are not loaded automatically. Set them manually, e.g. `$env:ADMIN_EMAIL="..."`, `$env:ADMIN_PASSWORD="..."`, `$env:SECRET_KEY="..."` before `flask --app app init-db`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-only-change-me` | Session signing key. **Set a long random value.** |
| `DATABASE_PATH` | `slotflow.db` | SQLite file location |
| `HOLD_MINUTES` | `15` | How long a slot is held before it expires |
| `ADMIN_EMAIL` | – | Admin e-mail created by `init-db` |
| `ADMIN_PASSWORD` | – | Admin password created by `init-db` |
| `PORT` | `5000` | Port used by `python app.py` |

## Database and admin user

```bash
flask --app app init-db            # create tables + seed 4 rooms (+ admin if ADMIN_* are set)
flask --app app create-admin --email you@example.com --password 'long-password'
```

`create-admin` creates the user or **resets the password** if the e-mail already exists.
Sign in on the main page, then use the **Admin** button in the header (or open `/admin`).

Tables: `users`, `rooms`, `bookings`. Booking statuses: `pending` (hold), `confirmed`, `cancelled`, `expired`.

## API

All endpoints return JSON. Authenticated endpoints use the session cookie.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/register` | – | Create account `{name, email, password}` |
| POST | `/api/login` | – | Sign in `{email, password}` |
| POST | `/api/logout` | – | Sign out |
| GET | `/api/me` | – | Current user or `null` |
| GET | `/api/rooms` | – | Rooms with slot availability for 3 days |
| POST | `/api/bookings` | user | Create a hold `{room_id, day (0-2), slot}` |
| POST | `/api/bookings/<id>/confirm` | owner | Confirm an active hold |
| POST | `/api/bookings/<id>/cancel` | owner | Cancel a hold or booking |
| GET | `/api/bookings/mine` | user | Active bookings of the current user |
| GET | `/api/admin/overview?status=&q=` | admin | KPIs, timeline grid and bookings feed |

## Tests

```bash
python smoke_test.py
```

Runs against a temporary database and checks registration, hold, double-booking protection, ownership checks, confirmation, cancellation, hold expiry and admin access control. Prints `ALL OK` on success.

## Troubleshooting

| Problem | Fix |
|---|---|
| `403` on `http://127.0.0.1:5000` (macOS) | AirPlay Receiver occupies the port. Use `PORT=5001`. |
| `Invalid email or password` for the admin | Reset it: `flask --app app create-admin --email ... --password ...`. `init-db` only sets the admin password when it runs. |
| Admin created in a different database | Run all commands from the folder that contains `app.py`, or set an absolute `DATABASE_PATH`. |
| Photos not showing | Check that the files exist in `static/img/`; hard-refresh the page (Ctrl+F5 / Cmd+Shift+R). |

## Limitations and ideas

- Time slots are fixed per room and the same for all three days
- The admin panel has the Overview page only (no statistics or room management)
- No e-mail notifications or payment; amounts are calculated from the hourly price
- For production use a WSGI server (e.g. Gunicorn) behind HTTPS, a strong `SECRET_KEY`, and a production database

## Credits

The visual design is a recreation of a design preview of the same name; backend, database schema, API and business logic are implemented from scratch. The photos are not original work: replace the files in `static/img/` with your own or properly licensed images before publishing the project publicly.