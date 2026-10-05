from django.contrib import admin

from .models import Achievement, UserAchievement

admin.site.register(Achievement)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "earned_at")
    list_filter = ("achievement",)
    date_hierarchy = "earned_at"
