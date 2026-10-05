from django.contrib import admin

from .models import JobMatch, Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "user", "created_at")
    search_fields = ("title", "company")


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ("resume", "vacancy", "score", "created_at")
    list_filter = ("created_at",)
