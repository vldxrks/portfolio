from django.contrib import admin

from .models import HabitCompletion


@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display = ("habit", "date", "value", "completed_at")
    list_filter = ("date",)
    search_fields = ("habit__name",)
    date_hierarchy = "date"
    autocomplete_fields = ("habit",)
