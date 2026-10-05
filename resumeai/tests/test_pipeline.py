import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.ai.providers import AIProviderError
from apps.ai.providers.base import AIProvider, Usage
from apps.jobs.matching import EmptyVacancy, match_resume_to_vacancy
from apps.resumes.models import Resume, ResumeAnalysis
from apps.resumes.services import analysis as svc
from apps.resumes.services.uploads import create_resume
from apps.resumes.services.validation import FileValidationError, validate_upload


def test_validation_rejects_bad_files(settings):
    with pytest.raises(FileValidationError):
        validate_upload(SimpleUploadedFile("a.exe", b"MZ..."))
    with pytest.raises(FileValidationError):
        validate_upload(SimpleUploadedFile("a.pdf", b""))
    with pytest.raises(FileValidationError):  # extension lies about content
        validate_upload(SimpleUploadedFile("a.pdf", b"not really a pdf at all"))
    settings.MAX_UPLOAD_SIZE = 10
    with pytest.raises(FileValidationError):
        validate_upload(SimpleUploadedFile("a.pdf", b"%PDF-1.4 plus a lot more bytes"))


@pytest.mark.django_db
@pytest.mark.parametrize("fixture,kind", [("pdf_file", "pdf"), ("docx_file", "docx")])
def test_extract_and_analyze(request, user, fixture, kind):
    f = request.getfixturevalue(fixture)
    resume = create_resume(user, f, validate_upload(f))
    assert resume.status == Resume.Status.COMPLETED
    assert "Django" in resume.extracted_text
    analysis = svc.create_analysis(resume)
    analysis.refresh_from_db()
    assert analysis.status == ResumeAnalysis.Status.COMPLETED, analysis.error_message
    assert 0 <= analysis.overall_score <= 100
    assert "Python" in str(analysis.result["skills"])
    assert analysis.result["candidate"]["email"] == "ivan@example.com"


@pytest.mark.django_db
def test_corrupted_pdf_marks_failed(user):
    f = SimpleUploadedFile("bad.pdf", b"%PDF-1.4 garbage garbage garbage")
    resume = create_resume(user, f, validate_upload(f))
    assert resume.status == Resume.Status.FAILED
    assert resume.error_message


class BadJsonProvider(AIProvider):
    name = "bad"
    calls = 0

    def analyze_resume(self, text):
        type(self).calls += 1
        return '{"nope": true}', Usage()


class DownProvider(AIProvider):
    name = "down"
    calls = 0

    def analyze_resume(self, text):
        type(self).calls += 1
        raise AIProviderError("boom secret-key-123")


@pytest.mark.django_db
@pytest.mark.parametrize("provider,message", [(BadJsonProvider, "Invalid AI response"),
                                              (DownProvider, "AI temporarily unavailable")])
def test_ai_failures_retry_and_hide_internals(monkeypatch, user, docx_file, provider, message):
    resume = create_resume(user, docx_file, "docx")
    provider.calls = 0
    monkeypatch.setattr(svc, "get_provider", lambda: provider())
    analysis = svc.create_analysis(resume)
    analysis.refresh_from_db()
    assert analysis.status == ResumeAnalysis.Status.FAILED
    assert analysis.error_message == message
    assert "secret" not in analysis.error_message
    assert provider.calls == 3  # bounded retries


@pytest.mark.django_db
def test_rate_limit(settings, user, docx_file):
    settings.ANALYSES_PER_HOUR = 1
    resume = create_resume(user, docx_file, "docx")
    svc.create_analysis(resume)
    with pytest.raises(svc.RateLimitExceeded):
        svc.create_analysis(resume)


def test_matching_is_explainable():
    result = {"skills": {"technical": ["Python", "Postgres", "Django"]}, "experience": [], "projects": []}
    m = match_resume_to_vacancy(result, "", "Python Backend Developer\nRequirements: Python, Django, PostgreSQL, Kubernetes")
    assert "PostgreSQL" in m["matched_skills"]  # alias Postgres -> PostgreSQL
    assert "Kubernetes" in m["missing_skills"]
    assert m["score"] == 75
    assert "heuristic" in m["explanation"]
    with pytest.raises(EmptyVacancy):
        match_resume_to_vacancy(result, "", "   ")
