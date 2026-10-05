from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters import rest_framework as filters
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.tracking.models import HabitCompletion

from .models import Habit
from .services import habit_service as svc
from .services import streak_service as streaks


class HabitSerializer(serializers.ModelSerializer):
    current_streak = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = [
            "id",
            "name",
            "description",
            "category",
            "color",
            "icon",
            "frequency",
            "weekdays",
            "target_count",
            "target_value",
            "unit",
            "start_date",
            "end_date",
            "is_active",
            "reminder_enabled",
            "reminder_time",
            "created_at",
            "current_streak",
        ]
        read_only_fields = ["id", "created_at", "is_active"]

    def get_current_streak(self, obj) -> int:
        return streaks.calculate_current_streak(obj, obj.user.local_today())

    def validate(self, attrs):
        instance = self.instance or Habit(user=self.context["request"].user)
        for k, v in attrs.items():
            setattr(instance, k, v)
        try:
            instance.clean()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict) from e
        return attrs


class CompleteSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)


class CompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitCompletion
        fields = ["date", "value", "note", "completed_at"]


class HabitFilter(filters.FilterSet):
    class Meta:
        model = Habit
        fields = ["category", "is_active", "frequency"]


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    filterset_class = HabitFilter
    search_fields = ["name", "description", "category"]
    ordering_fields = ["created_at", "name"]
    ordering = ["name"]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).select_related("user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.archive()  # soft delete: history is preserved

    @action(detail=True, methods=["post"], serializer_class=CompleteSerializer)
    def complete(self, request, pk=None):
        habit = self.get_object()
        ser = CompleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            c = svc.complete_habit(
                habit, ser.validated_data.get("date"), ser.validated_data.get("value"), ser.validated_data.get("note", "")
            )
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages}) from e
        return Response(CompletionSerializer(c).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], serializer_class=CompletionSerializer)
    def statistics(self, request, pk=None):
        habit = self.get_object()
        today = habit.user.local_today()
        done = streaks.done_dates(habit)
        return Response(
            {
                "current_streak": streaks.calculate_current_streak(habit, today, done),
                "longest_streak": streaks.calculate_longest_streak(habit, done),
                "total_completed_days": len(done),
                "completion_rate_30d": streaks.calculate_completion_rate(habit, today),
            }
        )

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        habit = self.get_object()
        habit.restore()
        return Response(self.get_serializer(habit).data)
