from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.achievements.models import UserAchievement
from apps.analytics.services import summary
from apps.tracking.models import HabitCompletion

from .forms import HabitForm
from .models import Habit
from .services import habit_service as svc
from .services import streak_service as streaks


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html")


def _own_habit(request, pk: int) -> Habit:
    return get_object_or_404(Habit.objects.select_related("user"), pk=pk, user=request.user)


@login_required
def dashboard(request):
    today = request.user.local_today()
    habits = [h for h in request.user.habits.filter(is_active=True) if h.is_scheduled_on(today)]
    todays = {c.habit_id: c for c in HabitCompletion.objects.filter(habit__in=habits, date=today)}
    cards = []
    for h in habits:
        c = todays.get(h.id)
        value = c.value if c else 0
        cards.append(
            {
                "habit": h,
                "value": value,
                "done": bool(c and c.value >= h.target_value),
                "percent": min(100, int(100 * value / h.target_value)),
                "streak": streaks.calculate_current_streak(h, today),
            }
        )
    done = sum(c["done"] for c in cards)
    ctx = {
        "cards": cards,
        "done": done,
        "total": len(cards),
        "percent": int(100 * done / len(cards)) if cards else 0,
        "best_streak": max((c["streak"] for c in cards), default=0),
        "xp_in_level": request.user.xp % 100,
    }
    return render(request, "habits/dashboard.html", ctx)


@login_required
def habit_list(request):
    q = request.GET.get("q", "").strip()
    show_archived = request.GET.get("archived") == "1"
    qs = request.user.habits.filter(is_active=not show_archived)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q))
    return render(request, "habits/list.html", {"habits": qs, "q": q, "archived": show_archived})


@login_required
def habit_create(request):
    form = HabitForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        habit = form.save()
        messages.success(request, "Habit created.")
        return redirect("habit-detail", pk=habit.pk)
    return render(request, "habits/form.html", {"form": form, "title": "New habit"})


@login_required
def habit_edit(request, pk):
    habit = _own_habit(request, pk)
    form = HabitForm(request.POST or None, instance=habit, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Habit updated.")
        return redirect("habit-detail", pk=habit.pk)
    return render(request, "habits/form.html", {"form": form, "title": "Edit habit"})


@login_required
def habit_detail(request, pk):
    habit = _own_habit(request, pk)
    today = request.user.local_today()
    done = streaks.done_dates(habit)
    history = habit.completions.all()[:30]
    ctx = {
        "habit": habit,
        "history": history,
        "current": streaks.calculate_current_streak(habit, today, done),
        "longest": streaks.calculate_longest_streak(habit, done),
        "total_days": len(done),
        "rate": streaks.calculate_completion_rate(habit, today),
    }
    return render(request, "habits/detail.html", ctx)


@login_required
@require_POST
def habit_complete(request, pk):
    habit = _own_habit(request, pk)
    try:
        svc.complete_habit(habit)
        messages.success(request, f"Nice! Progress saved for “{habit.name}”.")
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
    return redirect(request.POST.get("next") or "dashboard")


@login_required
@require_POST
def habit_archive(request, pk):
    habit = _own_habit(request, pk)
    habit.restore() if not habit.is_active else habit.archive()
    messages.info(request, "Habit updated.")
    return redirect("habit-list")


@login_required
def analytics_page(request):
    return render(request, "habits/analytics.html", {"data": summary(request.user, request.user.local_today())})


@login_required
def achievements_page(request):
    earned = UserAchievement.objects.filter(user=request.user).select_related("achievement")
    return render(request, "habits/achievements.html", {"earned": earned})


@login_required
def notifications_page(request):
    if request.method == "POST":
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect("notifications")
    return render(request, "habits/notifications.html", {"items": request.user.notifications.all()[:50]})


@login_required
def export_csv(request):
    import csv

    from django.http import HttpResponse

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="habitflow_completions.csv"'
    w = csv.writer(resp)
    w.writerow(["habit", "date", "value", "note"])
    qs = HabitCompletion.objects.filter(habit__user=request.user).select_related("habit")
    for c in qs.iterator():
        w.writerow([c.habit.name, c.date, c.value, c.note])
    return resp


def health(request):
    from django.db import connection
    from django.http import JsonResponse

    status = {"status": "ok", "database": "ok", "redis": "skipped"}
    try:
        connection.ensure_connection()
    except Exception:
        status.update(status="error", database="error")
    try:
        import redis
        from django.conf import settings

        redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1).ping()
        status["redis"] = "ok"
    except Exception:
        status["redis"] = "error"
    return JsonResponse(status, status=200 if status["database"] == "ok" else 503)
