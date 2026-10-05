# HabitFlow

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Django](https://img.shields.io/badge/Django-5-green) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue) ![Docker](https://img.shields.io/badge/Docker-compose-2496ED) ![Tests](https://img.shields.io/badge/tests-pytest-brightgreen) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

Habit tracker built as a Django modular monolith: timezone-aware streaks, numeric goals, analytics, achievements, Celery reminders and a JWT-secured REST API.

## Features
- Custom user model (unique email, timezone), registration, login by username or email, password change
- Habits: categories, colors, schedules (daily / chosen weekdays / N times per week), numeric goals with units (e.g. 7,500 / 10,000 steps)
- Completion tracking (one row per habit per local day, progress accumulates), XP and levels
- Streak engine computed from completion records (current, longest, completion rate), unit-tested for edge cases
- Dashboard, habit detail, analytics (Chart.js), achievements, in-app notifications, CSV export
- Archive / restore (soft delete, history preserved)
- Celery + Redis: per-minute reminders in the user's timezone, daily notification cleanup
- REST API (DRF): JWT, filtering, search, ordering, pagination, throttling, Swagger docs
- `/health/` endpoint (DB + Redis), dark / light / system theme, responsive Bootstrap 5 UI

## Tech Stack
Python 3.12, Django 5, DRF, SimpleJWT, drf-spectacular, django-filter, PostgreSQL 16, Celery, Redis, Docker Compose, pytest, factory_boy, Ruff, GitHub Actions.

## Architecture
```
config/            settings (base/development/production/test), urls, celery
apps/users/        custom User, auth backend, registration
apps/habits/       Habit model, forms, views, API, services/ (habit_service, streak_service)
apps/tracking/     HabitCompletion (UniqueConstraint habit+date)
apps/achievements/ Achievement, UserAchievement, awarding service
apps/notifications/ Notification model, Celery tasks, context processor
apps/analytics/    aggregation services
```
Business logic lives in `services/`; views and API viewsets stay thin. Streaks are computed, not stored.

## Getting Started
```bash
cp .env.example .env
docker compose up --build
make seed        # demo data
```
App: http://localhost:8000 · Admin: `/admin/` (`make createsuperuser`).

## Demo Account
Created only by `python manage.py seed_demo` (never automatically): `demo@example.com` / `DemoPassword123!`. For local demos only.

## API
```bash
curl -X POST localhost:8000/api/v1/auth/token/ -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"DemoPassword123!"}'
curl localhost:8000/api/v1/habits/?category=fitness -H "Authorization: Bearer $TOKEN"
curl -X POST localhost:8000/api/v1/habits/ -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Read","category":"learning","target_value":30,"unit":"pages"}'
curl -X POST localhost:8000/api/v1/habits/1/complete/ -H "Authorization: Bearer $TOKEN"
```
Endpoints: `/api/v1/auth/token/`, `/auth/token/refresh/`, `/habits/`, `/habits/{id}/complete|statistics|restore/`, `/analytics/`, `/achievements/`, `/profile/`.
Swagger UI: `/api/docs/`, schema: `/api/schema/`.

## Testing & Code Quality
```bash
pip install -r requirements-dev.txt
pytest            # coverage enforced at 80% in CI
ruff check .
```
CI (GitHub Actions) runs lint and tests against PostgreSQL and Redis services.

## Screenshots
Add images to `screenshots/`: landing, dashboard, habit-detail, analytics, mobile.

## Future Improvements
Habit wizard, calendar heatmap, CSV import, full Russian translation, email reminders, nginx + gunicorn production compose.

## License
MIT
