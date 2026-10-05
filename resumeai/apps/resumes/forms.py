from django import forms

from apps.jobs.models import Vacancy

from .services.validation import FileValidationError, validate_upload


class UploadForm(forms.Form):
    title = forms.CharField(max_length=200, required=False)
    file = forms.FileField()

    def clean_file(self):
        f = self.cleaned_data["file"]
        try:
            self.file_type = validate_upload(f)
        except FileValidationError as exc:
            raise forms.ValidationError(exc.message) from exc
        return f


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ("title", "company", "url", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 10})}

    def clean_description(self):
        d = self.cleaned_data["description"].strip()
        if not d:
            raise forms.ValidationError("Job description is empty.")
        return d
