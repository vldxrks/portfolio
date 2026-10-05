import io
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="resumeai_test_media_")
os.environ["PRIVATE_MEDIA_ROOT"] = _TMP
os.environ.setdefault("ANALYSIS_SYNC", "True")
os.environ["AI_PROVIDER"] = "local"

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from docx import Document
from reportlab.pdfgen import canvas

RESUME_LINES = [
    "Ivan Petrenko",
    "ivan@example.com | +380501234567 | Kyiv, Ukraine",
    "github.com/ivanp",
    "Summary",
    "Junior Python backend developer.",
    "Skills",
    "Python, Django, PostgreSQL, Docker, Git, REST API, Postgres",
    "Experience",
    "Backend Developer, Acme (2024 - 2025)",
    "Built REST APIs with Django REST Framework and PostgreSQL.",
    "Education",
    "Bugay University, Software Engineering, 2022 - 2026",
    "Languages",
    "English B2, Ukrainian native",
]


@pytest.fixture(autouse=True)
def _sync(settings):
    settings.ANALYSIS_SYNC = True
    settings.AI_PROVIDER = "local"
    settings.AI_BACKOFF_SECONDS = 0
    settings.ANALYSES_PER_HOUR = 100


def make_docx_bytes(lines=RESUME_LINES) -> bytes:
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_pdf_bytes(lines=RESUME_LINES) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


@pytest.fixture
def docx_file():
    return SimpleUploadedFile("cv.docx", make_docx_bytes(),
                              content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@pytest.fixture
def pdf_file():
    return SimpleUploadedFile("cv.pdf", make_pdf_bytes(), content_type="application/pdf")


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="vlad", email="vlad@example.com", password="Str0ng-pass-123")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(username="eve", email="eve@example.com", password="Str0ng-pass-123")


@pytest.fixture
def api(user):
    from rest_framework.test import APIClient

    client = APIClient()
    resp = client.post("/api/v1/auth/token/", {"username": "vlad", "password": "Str0ng-pass-123"}, format="json")
    assert resp.status_code == 200, resp.content
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client
