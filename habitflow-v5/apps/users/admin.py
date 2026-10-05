from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class HabitUserAdmin(UserAdmin):
    list_display = ("username", "email", "timezone", "xp", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("HabitFlow", {"fields": ("avatar", "timezone", "xp")}),)
