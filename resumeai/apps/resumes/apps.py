from django.apps import AppConfig


class ResumesConfig(AppConfig):
    name = "apps.resumes"

    def ready(self):
        from . import signals  # noqa: F401
