import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Avg, Count
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.forms import RegisterForm
from apps.jobs.matching import EmptyVacancy
from apps.jobs.models import JobMatch, Vacancy
from apps.jobs.services import run_match

from .forms import UploadForm, VacancyForm
from .models import Resume, ResumeAnalysis
from .services.analysis import RateLimitExceeded, create_analysis
from .services.uploads import create_resume_and_analyze

SCORE_LABELS = {"ats_readiness": "ATS readiness"}

def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html")


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("landing")


def health(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        db = "ok"
    except Exception:
        db = "error"
    return JsonResponse({"status": "ok" if db == "ok" else "error", "database": db},
                        status=200 if db == "ok" else 503)


@login_required
def dashboard(request):
    resumes = Resume.objects.filter(user=request.user).annotate(n_analyses=Count("analyses"))
    analyses = ResumeAnalysis.objects.filter(resume__user=request.user, status="completed")
    stats = {
        "resumes": resumes.count(),
        "analyses": analyses.count(),
        "avg_score": analyses.aggregate(a=Avg("overall_score"))["a"],
        "matches": JobMatch.objects.filter(user=request.user).count(),
    }
    latest = {a.resume_id: a for a in analyses.order_by("created_at")}  # last write wins = newest
    for r in resumes:
        r.last_analysis = latest.get(r.id)
    vacancies = Vacancy.objects.filter(user=request.user)[:5]
    return render(request, "dashboard.html", {"resumes": resumes, "stats": stats, "vacancies": vacancies})


@login_required
def upload(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            resume, analysis = create_resume_and_analyze(
                request.user, form.cleaned_data["file"], form.file_type, form.cleaned_data["title"])
        except RateLimitExceeded as exc:
            messages.error(request, str(exc))
            return redirect("dashboard")
        if resume.status == Resume.Status.FAILED:
            messages.error(request, resume.error_message)
        return redirect("resume_detail", pk=resume.pk)
    return render(request, "resumes/upload.html", {"form": form})


def _own_resume(request, pk):
    return get_object_or_404(Resume, pk=pk, user=request.user)  # 404 for other users' resumes


@login_required
def resume_detail(request, pk):
    resume = _own_resume(request, pk)
    analyses = list(resume.analyses.all())
    current = analyses[0] if analyses else None
    done = next((a for a in analyses if a.status == "completed"), None)
    return render(request, "resumes/detail.html", {
        "resume": resume, "analyses": analyses, "current": current, "done": done,
        "result": done.result if done else None,
        "scores": [(SCORE_LABELS.get(k, k.replace("_", " ").capitalize()), v) for k, v in done.result["scores"].items()]
        if done else [],
        "vacancies": Vacancy.objects.filter(user=request.user),
        "matches": resume.matches.select_related("vacancy"),
        "in_progress": bool(current and current.status in ("queued", "processing")),
    })


@login_required
@require_POST
def resume_analyze(request, pk):
    resume = _own_resume(request, pk)
    try:
        create_analysis(resume)
    except RateLimitExceeded as exc:
        messages.error(request, str(exc))
    return redirect("resume_detail", pk=pk)


@login_required
@require_POST
def resume_delete(request, pk):
    _own_resume(request, pk).delete()
    messages.success(request, "Resume and all related data deleted.")
    return redirect("dashboard")


@login_required
def resume_file(request, pk):
    resume = _own_resume(request, pk)
    if not resume.file:
        raise Http404
    return FileResponse(resume.file.open("rb"), as_attachment=True, filename=resume.original_filename)


@login_required
def analysis_status(request, pk):
    a = get_object_or_404(ResumeAnalysis, pk=pk, resume__user=request.user)
    return JsonResponse({"status": a.status, "step": a.step, "error": a.error_message})


@login_required
def analysis_export(request, pk):
    a = get_object_or_404(ResumeAnalysis, pk=pk, resume__user=request.user, status="completed")
    resp = HttpResponse(json.dumps(a.result, ensure_ascii=False, indent=2), content_type="application/json")
    resp["Content-Disposition"] = f'attachment; filename="analysis-{a.pk}.json"'
    return resp


@login_required
@require_POST
def delete_account(request):
    user = request.user
    logout(request)
    user.delete()  # cascades to resumes (files removed via signal), analyses, vacancies, matches
    return redirect("landing")


# ---- vacancies ----
@login_required
def vacancy_list(request):
    return render(request, "jobs/list.html", {"vacancies": Vacancy.objects.filter(user=request.user)})


@login_required
def vacancy_create(request):
    form = VacancyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        v = form.save(commit=False)
        v.user = request.user
        v.save()
        return redirect("vacancy_list")
    return render(request, "jobs/create.html", {"form": form})


@login_required
@require_POST
def vacancy_delete(request, pk):
    get_object_or_404(Vacancy, pk=pk, user=request.user).delete()
    return redirect("vacancy_list")


@login_required
@require_POST
def match_create(request, pk):
    resume = _own_resume(request, pk)
    vacancy = get_object_or_404(Vacancy, pk=request.POST.get("vacancy"), user=request.user)
    try:
        match = run_match(request.user, resume, vacancy)
    except (EmptyVacancy, ValueError) as exc:
        messages.error(request, str(exc))
        return redirect("resume_detail", pk=pk)
    return redirect("match_detail", pk=match.pk)


@login_required
def match_detail(request, pk):
    match = get_object_or_404(JobMatch.objects.select_related("resume", "vacancy"), pk=pk, user=request.user)
    return render(request, "jobs/match.html", {"match": match})
