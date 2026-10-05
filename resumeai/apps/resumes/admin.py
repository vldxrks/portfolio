from django.contrib import admin

from .models import Resume, ResumeAnalysis


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "file_type", "status", "created_at")
    list_filter = ("status", "file_type")
    search_fields = ("title", "original_filename", "user__username")
    readonly_fields = ("file_hash", "extracted_text", "created_at")
    date_hierarchy = "created_at"


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "resume", "status", "overall_score", "model", "input_tokens", "output_tokens", "created_at")
    list_filter = ("status", "provider", "model")
    readonly_fields = ("result", "created_at", "finished_at")
    date_hierarchy = "created_at"
