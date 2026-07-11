"""Login form working with phone-number usernames."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from accounts.phone import normalize_phone


class TelefonKirishForm(AuthenticationForm):
    username = forms.CharField(
        label="Telefon raqam",
        widget=forms.TextInput(
            attrs={"placeholder": "+998901234567", "autofocus": True}
        ),
    )
    password = forms.CharField(label="Parol", widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": "Telefon raqam yoki parol noto'g'ri.",
        "inactive": "Bu foydalanuvchi faol emas.",
    }

    def clean_username(self) -> str:
        return normalize_phone(self.cleaned_data["username"])
