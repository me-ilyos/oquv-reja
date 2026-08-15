from django import forms

from accounts.models import Department


class KafedraForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["nomi", "fakultet"]
        labels = {"nomi": "Kafedra nomi", "fakultet": "Fakultet nomi"}
