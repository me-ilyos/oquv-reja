"""Forms for creating (via Excel upload) and correcting an o'quv reja."""

from django import forms

from plans.models import OquvReja
from plans.uploads import YuklashParametrlari


class RejaImportForm(forms.Form):
    fayl = forms.FileField(
        label="Excel fayl (.xlsx)",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
    )
    boshlanish_yili = forms.IntegerField(
        label="Boshlanish yili",
        required=False,
        min_value=2000,
        max_value=2100,
        help_text="Bo'sh qoldirilsa fayldan o'qiladi",
    )
    talabalar_soni = forms.IntegerField(label="Talabalar soni", min_value=1)
    guruhlar_soni = forms.IntegerField(label="Guruhlar soni", min_value=1)
    guruh_prefiksi = forms.CharField(
        label="Guruh prefiksi",
        required=False,
        max_length=20,
        help_text="Masalan: DI. Bo'sh qoldirilsa yo'nalish kodi ishlatiladi",
    )
    replace = forms.BooleanField(label="Mavjud rejani almashtirish", required=False)

    def parametrlar(self) -> YuklashParametrlari:
        return YuklashParametrlari(
            talabalar_soni=self.cleaned_data["talabalar_soni"],
            guruhlar_soni=self.cleaned_data["guruhlar_soni"],
            guruh_prefiksi=self.cleaned_data["guruh_prefiksi"],
            boshlanish_yili=self.cleaned_data["boshlanish_yili"],
            replace=self.cleaned_data["replace"],
        )


class RejaTahrirForm(forms.ModelForm):
    class Meta:
        model = OquvReja
        fields = ["yonalish_nomi", "talabalar_soni", "guruhlar_soni", "guruh_prefiksi"]
        labels = {
            "yonalish_nomi": "Yo'nalish nomi",
            "talabalar_soni": "Talabalar soni",
            "guruhlar_soni": "Guruhlar soni",
            "guruh_prefiksi": "Guruh prefiksi",
        }
