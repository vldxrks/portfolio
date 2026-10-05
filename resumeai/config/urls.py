from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.resumes import api, views

router = DefaultRouter()
router.register("resumes", api.ResumeViewSet, basename="resume")
router.register("jobs", api.VacancyViewSet, basename="job")
router.register("matches", api.MatchViewSet, basename="match")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health),
    path("", views.landing, name="landing"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("resumes/upload/", views.upload, name="upload"),
    path("resumes/<int:pk>/", views.resume_detail, name="resume_detail"),
    path("resumes/<int:pk>/analyze/", views.resume_analyze, name="resume_analyze"),
    path("resumes/<int:pk>/delete/", views.resume_delete, name="resume_delete"),
    path("resumes/<int:pk>/file/", views.resume_file, name="resume_file"),
    path("resumes/<int:pk>/match/", views.match_create, name="match_create"),
    path("analyses/<int:pk>/status/", views.analysis_status, name="analysis_status"),
    path("analyses/<int:pk>/export/", views.analysis_export, name="analysis_export"),
    path("matches/<int:pk>/", views.match_detail, name="match_detail"),
    path("jobs/", views.vacancy_list, name="vacancy_list"),
    path("jobs/create/", views.vacancy_create, name="vacancy_create"),
    path("jobs/<int:pk>/delete/", views.vacancy_delete, name="vacancy_delete"),
    path("account/delete/", views.delete_account, name="delete_account"),
    # API
    path("api/v1/auth/token/", TokenObtainPairView.as_view()),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/v1/matches/create/", api.MatchCreateView.as_view()),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
