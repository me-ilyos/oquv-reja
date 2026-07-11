from django import forms

from accounts.models import Department


class KafedraForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["nomi"]
        labels = {"nomi": "Kafedra nomi"}
