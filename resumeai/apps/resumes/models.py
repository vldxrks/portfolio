import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

private_storage = FileSystemStorage(location=str(settings.PRIVATE_MEDIA_ROOT))


def resume_upload_path(instance, filename):
    ext = Path(filename).suffix.lower()
    return f"resumes/{instance.user_id}/{uuid.uuid4().hex}{ext}"  # never trust the client filename


class Resume(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")
    title = models.CharField(max_length=200)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=resume_upload_path, storage=private_storage)
    file_type = models.CharField(max_length=8)
    file_size = models.PositiveIntegerField()
    file_hash = models.CharField(max_length=64, db_index=True)  # SHA-256
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPLOADED, db_index=True)
    extracted_text = models.TextField(blank=True)
    page_count = models.PositiveIntegerField(default=0)
    error_message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def latest_analysis(self):
        return self.analyses.filter(status=ResumeAnalysis.Status.COMPLETED).order_by("-created_at").first()


class ResumeAnalysis(models.Model):
    """One row per analysis run -> full history is kept when the user re-analyzes."""

    class Status(models.TextChoices):
        QUEUED = "queued"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="analyses")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED, db_index=True)
    step = models.CharField(max_length=60, blank=True)  # real step name, not a fake percentage
    result = models.JSONField(null=True, blank=True)  # validated ResumeAnalysisSchema
    overall_score = models.PositiveSmallIntegerField(null=True, blank=True)
    provider = models.CharField(max_length=30, blank=True)
    model = models.CharField(max_length=80, blank=True)
    prompt_version = models.CharField(max_length=40, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    error_message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "resume analyses"
