from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.habits import api, api_extra, views
from apps.users.views import register

router = DefaultRouter()
router.register("habits", api.HabitViewSet, basename="api-habit")

api_patterns = [
    path("auth/token/", api_extra.ThrottledTokenView.as_view(), name="token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("analytics/", api_extra.AnalyticsView.as_view()),
    path("achievements/", api_extra.AchievementsView.as_view()),
    path("profile/", api_extra.ProfileView.as_view()),
    path("", include(router.urls)),
]

urlpatterns = [
    path("", views.landing, name="landing"),
    path("health/", views.health, name="health"),
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("password-change/", auth_views.PasswordChangeView.as_view(success_url="/dashboard/"), name="password_change"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("habits/", views.habit_list, name="habit-list"),
    path("habits/create/", views.habit_create, name="habit-create"),
    path("habits/<int:pk>/", views.habit_detail, name="habit-detail"),
    path("habits/<int:pk>/edit/", views.habit_edit, name="habit-edit"),
    path("habits/<int:pk>/complete/", views.habit_complete, name="habit-complete"),
    path("habits/<int:pk>/archive/", views.habit_archive, name="habit-archive"),
    path("analytics/", views.analytics_page, name="analytics"),
    path("achievements/", views.achievements_page, name="achievements"),
    path("notifications/", views.notifications_page, name="notifications"),
    path("export/completions.csv", views.export_csv, name="export-csv"),
    path("api/v1/", include(api_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
