from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.jobs.matching import EmptyVacancy
from apps.jobs.models import JobMatch, Vacancy
from apps.jobs.services import run_match

from .models import Resume, ResumeAnalysis
from .serializers import (
    AnalysisSerializer,
    MatchCreateSerializer,
    MatchSerializer,
    ResumeSerializer,
    VacancySerializer,
)
from .services.analysis import RateLimitExceeded, create_analysis
from .services.uploads import create_resume_and_analyze


def error(code, message, http=400, details=None):
    return Response({"error": {"code": code, "message": message, "details": details or {}}}, status=http)


class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "original_filename"]
    ordering_fields = ["created_at", "title"]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):  # a user can only ever see their own resumes
        qs = Resume.objects.filter(user=self.request.user)
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st else qs

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            resume, analysis = create_resume_and_analyze(
                request.user, ser.validated_data["file"], ser.context["file_type"], ser.validated_data.get("title", ""))
        except RateLimitExceeded as exc:
            return error("RATE_LIMITED", str(exc), 429)
        data = ResumeSerializer(resume).data
        data["analysis_id"] = analysis.id if analysis else None
        return Response(data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=AnalysisSerializer)
    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        resume = self.get_object()
        try:
            analysis = create_analysis(resume)
        except RateLimitExceeded as exc:
            return error("RATE_LIMITED", str(exc), 429)
        return Response(AnalysisSerializer(analysis).data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(responses=AnalysisSerializer)
    @action(detail=True, methods=["get"])
    def analysis(self, request, pk=None):
        resume = self.get_object()
        analysis = resume.analyses.first()
        if not analysis:
            return error("NOT_FOUND", "No analysis yet.", 404)
        return Response(AnalysisSerializer(analysis).data)

    @extend_schema(responses=AnalysisSerializer(many=True))
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        return Response(AnalysisSerializer(self.get_object().analyses.all(), many=True).data)


class VacancyViewSet(viewsets.ModelViewSet):
    serializer_class = VacancySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "company", "description"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        qs = Vacancy.objects.filter(user=self.request.user)
        company = self.request.query_params.get("company")
        return qs.filter(company__icontains=company) if company else qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MatchViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MatchSerializer

    def get_queryset(self):
        return JobMatch.objects.filter(user=self.request.user).select_related("resume", "vacancy")


class MatchCreateView(APIView):
    @extend_schema(request=MatchCreateSerializer, responses=MatchSerializer)
    def post(self, request):
        ser = MatchCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        resume = Resume.objects.filter(user=request.user, id=ser.validated_data["resume"]).first()
        vacancy = Vacancy.objects.filter(user=request.user, id=ser.validated_data["vacancy"]).first()
        if not resume or not vacancy:
            return error("NOT_FOUND", "Resume or vacancy not found.", 404)
        try:
            match = run_match(request.user, resume, vacancy)
        except EmptyVacancy as exc:
            return error("INVALID_VACANCY", str(exc))
        except ValueError as exc:
            return error("NO_ANALYSIS", str(exc), 409)
        return Response(MatchSerializer(match).data, status=status.HTTP_201_CREATED)


__all__ = ["MatchCreateView", "MatchViewSet", "ResumeAnalysis", "ResumeViewSet", "VacancyViewSet"]
