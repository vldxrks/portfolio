from rest_framework import serializers

from apps.jobs.models import JobMatch, Vacancy

from .models import Resume, ResumeAnalysis
from .services.validation import FileValidationError, validate_upload


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAnalysis
        fields = ("id", "resume", "status", "step", "overall_score", "result", "model", "prompt_version",
                  "input_tokens", "output_tokens", "error_message", "created_at", "finished_at")
        read_only_fields = fields


class ResumeSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    title = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Resume
        fields = ("id", "title", "original_filename", "file", "file_type", "file_size", "status",
                  "page_count", "error_message", "created_at")
        read_only_fields = ("id", "original_filename", "file_type", "file_size", "status", "page_count",
                            "error_message", "created_at")

    def validate_file(self, f):
        try:
            self.context["file_type"] = validate_upload(f)
        except FileValidationError as exc:
            raise serializers.ValidationError({"code": exc.code, "message": exc.message}) from exc
        return f


class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = ("id", "title", "company", "description", "url", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Job description is empty.")
        return value


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMatch
        fields = ("id", "resume", "vacancy", "score", "required_skills", "matched_skills", "missing_skills",
                  "related_skills", "explanation", "created_at")
        read_only_fields = fields


class MatchCreateSerializer(serializers.Serializer):
    resume = serializers.IntegerField()
    vacancy = serializers.IntegerField()
