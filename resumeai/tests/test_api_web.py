import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.resumes.models import Resume
from tests.conftest import make_docx_bytes

pytestmark = pytest.mark.django_db
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def upload(api, name="cv.docx", data=None):
    data = data if data is not None else make_docx_bytes()
    return api.post("/api/v1/resumes/", {"file": SimpleUploadedFile(name, data, content_type=DOCX)}, format="multipart")


def test_api_requires_auth():
    assert APIClient().get("/api/v1/resumes/").status_code == 401


def test_api_full_flow(api):
    r = upload(api)
    assert r.status_code == 201, r.content
    rid, aid = r.data["id"], r.data["analysis_id"]
    a = api.get(f"/api/v1/resumes/{rid}/analysis/")
    assert a.status_code == 200 and a.data["status"] == "completed" and a.data["id"] == aid
    v = api.post("/api/v1/jobs/", {"title": "Python Dev", "description": "Python, Django, Kubernetes, Docker"},
                 format="json")
    assert v.status_code == 201
    m = api.post("/api/v1/matches/create/", {"resume": rid, "vacancy": v.data["id"]}, format="json")
    assert m.status_code == 201, m.content
    assert "Kubernetes" in m.data["missing_skills"] and "Django" in m.data["matched_skills"]
    assert api.get("/api/v1/resumes/?search=cv").data["count"] == 1
    assert api.get("/api/v1/resumes/?status=failed").data["count"] == 0
    assert api.get(f"/api/v1/resumes/{rid}/history/").status_code == 200


def test_api_error_format(api):
    r = upload(api, "x.exe", b"MZ junk")
    assert r.status_code == 400
    assert "error" in r.data and "code" in r.data["error"]


def test_users_cannot_see_each_others_data(api, other_user):
    rid = upload(api).data["id"]
    vid = api.post("/api/v1/jobs/", {"title": "T", "description": "Python"}, format="json").data["id"]
    eve = APIClient()
    eve.force_authenticate(other_user)
    assert eve.get(f"/api/v1/resumes/{rid}/").status_code == 404
    assert eve.get(f"/api/v1/resumes/{rid}/analysis/").status_code == 404
    assert eve.delete(f"/api/v1/resumes/{rid}/").status_code == 404
    assert eve.get(f"/api/v1/jobs/{vid}/").status_code == 404
    assert eve.post("/api/v1/matches/create/", {"resume": rid, "vacancy": vid}, format="json").status_code == 404
    assert eve.get("/api/v1/resumes/").data["count"] == 0


def test_delete_resume_removes_file(api):
    rid = upload(api).data["id"]
    path = Resume.objects.get(id=rid).file.path
    assert os.path.exists(path)
    assert api.delete(f"/api/v1/resumes/{rid}/").status_code == 204
    assert not os.path.exists(path)


def test_web_flow_and_private_file(client, user, other_user):
    assert client.get("/dashboard/").status_code == 302  # login required
    assert client.post("/register/", {"username": "new", "email": "new@example.com",
                                      "password1": "Str0ng-pass-123", "password2": "Str0ng-pass-123"}).status_code == 302
    client.logout()
    client.force_login(user)
    r = client.post("/resumes/upload/", {"file": SimpleUploadedFile("cv.docx", make_docx_bytes(), content_type=DOCX)})
    assert r.status_code == 302, r.content[:500]
    resume = Resume.objects.get(user=user)
    assert client.get(f"/resumes/{resume.id}/").status_code == 200
    assert client.get("/dashboard/").status_code == 200
    assert client.get(f"/resumes/{resume.id}/file/").status_code == 200
    analysis = resume.latest_analysis
    assert client.get(f"/analyses/{analysis.id}/status/").json()["status"] == "completed"
    assert client.get(f"/analyses/{analysis.id}/export/").status_code == 200
    client.force_login(other_user)
    assert client.get(f"/resumes/{resume.id}/file/").status_code == 404
    assert client.get(f"/resumes/{resume.id}/").status_code == 404
    assert client.get(f"/analyses/{analysis.id}/export/").status_code == 404


def test_health_and_docs(client):
    assert client.get("/health/").status_code == 200
    assert client.get("/api/schema/").status_code == 200
    assert client.get("/api/docs/").status_code == 200
