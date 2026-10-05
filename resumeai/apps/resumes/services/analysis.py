"""Analysis pipeline: text -> AI provider -> Pydantic validation -> save. Logs never contain resume text."""
import hashlib
import logging
import threading
import time
from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from pydantic import ValidationError

from apps.ai.prompts import RESUME_ANALYSIS_PROMPT_VERSION
from apps.ai.providers import AIProviderError, get_provider
from apps.ai.schemas import ResumeAnalysisSchema
from apps.resumes.models import Resume, ResumeAnalysis

from .extraction import ExtractionError, extract_text
from .text_processing import clean_text

log = logging.getLogger("resumeai.analysis")


class RateLimitExceeded(Exception):
    pass


def process_upload(resume: Resume) -> None:
    """Extract text right after upload (fast, local). Marks the resume failed with a clear message."""
    try:
        text, pages = extract_text(resume.file.path, resume.file_type)
        resume.extracted_text = clean_text(text, settings.AI_MAX_INPUT_CHARS)
        resume.page_count = pages
        resume.status = Resume.Status.COMPLETED
        resume.error_message = ""
    except ExtractionError as exc:
        resume.status = Resume.Status.FAILED
        resume.error_message = str(exc)
    resume.save(update_fields=["extracted_text", "page_count", "status", "error_message"])


def file_sha256(f) -> str:
    h = hashlib.sha256()
    for chunk in f.chunks():
        h.update(chunk)
    f.seek(0)
    return h.hexdigest()


def create_analysis(resume: Resume) -> ResumeAnalysis:
    """Create a queued analysis (checks rate limit) and dispatch it."""
    since = timezone.now() - timedelta(hours=1)
    recent = ResumeAnalysis.objects.filter(resume__user=resume.user_id, created_at__gte=since).count()
    if recent >= settings.ANALYSES_PER_HOUR:
        raise RateLimitExceeded(f"Limit reached: {settings.ANALYSES_PER_HOUR} analyses per hour.")
    analysis = ResumeAnalysis.objects.create(
        resume=resume, prompt_version=RESUME_ANALYSIS_PROMPT_VERSION, provider=settings.AI_PROVIDER
    )
    dispatch(analysis.id)
    return analysis


def dispatch(analysis_id: int) -> None:
    """Background execution. Swap this one function for `task.delay()` to move to Celery."""
    if settings.ANALYSIS_SYNC:
        run_analysis(analysis_id)
        return

    def _worker():
        close_old_connections()
        try:
            run_analysis(analysis_id)
        finally:
            close_old_connections()

    threading.Thread(target=_worker, daemon=True).start()


def _set(analysis: ResumeAnalysis, **fields):
    for k, v in fields.items():
        setattr(analysis, k, v)
    analysis.save(update_fields=list(fields))


def _call_with_retry(provider, text: str):
    last_error = "Analysis failed"
    for attempt in range(1, settings.AI_MAX_ATTEMPTS + 1):
        try:
            raw, usage = provider.analyze_resume(text)
            return ResumeAnalysisSchema.model_validate_json(raw), usage
        except ValidationError:
            last_error = "Invalid AI response"
        except AIProviderError as exc:
            last_error = "AI temporarily unavailable"
            log.warning("provider error attempt=%s type=%s", attempt, exc)
        if attempt < settings.AI_MAX_ATTEMPTS:
            time.sleep(settings.AI_BACKOFF_SECONDS * 2 ** (attempt - 1))  # exponential backoff
    raise AIProviderError(last_error)


def run_analysis(analysis_id: int) -> None:
    analysis = ResumeAnalysis.objects.select_related("resume").get(id=analysis_id)
    resume = analysis.resume
    started = time.monotonic()
    try:
        _set(analysis, status=ResumeAnalysis.Status.PROCESSING, step="Preparing text")
        if not resume.extracted_text:
            raise AIProviderError(resume.error_message or "No text to analyze")
        provider = get_provider()
        _set(analysis, step="Analyzing resume", provider=provider.name)
        parsed, usage = _call_with_retry(provider, resume.extracted_text)
        _set(
            analysis,
            status=ResumeAnalysis.Status.COMPLETED,
            step="Done",
            result=parsed.model_dump(),
            overall_score=parsed.scores.overall,
            model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            finished_at=timezone.now(),
        )
        status = "completed"
    except Exception as exc:  # store a safe message; details stay in server logs
        msg = str(exc) if isinstance(exc, AIProviderError) else "Analysis failed"
        _set(analysis, status=ResumeAnalysis.Status.FAILED, step="Failed", error_message=msg[:300],
             finished_at=timezone.now())
        status = "failed"
        log.exception("analysis failed id=%s", analysis_id)
    log.info("analysis id=%s user=%s status=%s model=%s duration=%.2fs tokens_in=%s tokens_out=%s",
             analysis.id, resume.user_id, status, analysis.model, time.monotonic() - started,
             analysis.input_tokens, analysis.output_tokens)
