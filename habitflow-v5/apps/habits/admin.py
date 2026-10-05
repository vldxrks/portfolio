from django.contrib import admin

from .models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "frequency", "is_active", "created_at")
    list_filter = ("category", "frequency", "is_active")
    search_fields = ("name", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "archived_at")
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
