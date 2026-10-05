from django import forms

from .models import Habit

DAYS = [(0, "Mon"), (1, "Tue"), (2, "Wed"), (3, "Thu"), (4, "Fri"), (5, "Sat"), (6, "Sun")]


class HabitForm(forms.ModelForm):
    weekdays = forms.TypedMultipleChoiceField(choices=DAYS, coerce=int, required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Habit
        fields = [
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
            "reminder_enabled",
            "reminder_time",
        ]
        widgets = {
            "color": forms.TextInput(attrs={"type": "color"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reminder_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        for f in self.fields.values():
            if not isinstance(f.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                f.widget.attrs.setdefault("class", "form-control")

    def _post_clean(self):
        if self.user and not self.instance.pk:
            self.instance.user = self.user
        super()._post_clean()
