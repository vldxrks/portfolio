from rest_framework import serializers
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.achievements.models import UserAchievement
from apps.analytics.services import summary
from apps.users.models import User


class ThrottledTokenView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class AnalyticsView(APIView):
    def get(self, request):
        return Response(summary(request.user, request.user.local_today()))


class AchievementsView(APIView):
    def get(self, request):
        qs = UserAchievement.objects.filter(user=request.user).select_related("achievement")
        return Response([{"code": u.achievement.code, "title": u.achievement.title, "earned_at": u.earned_at} for u in qs])


class ProfileSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "timezone", "xp", "level"]
        read_only_fields = ["xp"]


class ProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user
