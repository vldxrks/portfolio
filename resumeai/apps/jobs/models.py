from django.conf import settings
from django.db import models


class Vacancy(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vacancies")
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "vacancies"

    def __str__(self):
        return f"{self.title} @ {self.company}" if self.company else self.title


class JobMatch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matches")
    resume = models.ForeignKey("resumes.Resume", on_delete=models.CASCADE, related_name="matches")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="matches")
    analysis = models.ForeignKey("resumes.ResumeAnalysis", on_delete=models.SET_NULL, null=True, blank=True)
    score = models.PositiveSmallIntegerField()
    required_skills = models.JSONField(default=list)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    related_skills = models.JSONField(default=dict)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
