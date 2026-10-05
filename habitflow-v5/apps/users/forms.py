from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "timezone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = "First name"
        self.fields["timezone"].initial = "Europe/Kyiv"
        autocomplete = {"username": "username", "email": "email", "first_name": "given-name",
                        "password1": "new-password", "password2": "new-password"}
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control", "placeholder": " "})
            if name in autocomplete:
                field.widget.attrs["autocomplete"] = autocomplete[name]
