"""Forms for creating (via Excel upload) and correcting an o'quv reja."""

from django import forms

from plans.models import OquvReja
from plans.uploads import YuklashParametrlari


class RejaImportForm(forms.Form):
    fayl = forms.FileField(
        label="Excel fayl (.xlsx)",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
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
            boshlanish_yili=None,
            replace=self.cleaned_data["replace"],
        )


class RejaTahrirForm(forms.ModelForm):
    class Meta:
        model = OquvReja
        fields = [
            "bilim_sohasi_kodi",
            "bilim_sohasi_nomi",
            "talim_sohasi_kodi",
            "talim_sohasi_nomi",
            "yonalish_kodi",
            "yonalish_nomi",
            "talim_shakli",
            "daraja",
            "talabalar_soni",
            "guruhlar_soni",
            "guruh_prefiksi",
        ]
        labels = {
            "bilim_sohasi_kodi": "Bilim sohasi kodi",
            "bilim_sohasi_nomi": "Bilim sohasi nomi",
            "talim_sohasi_kodi": "Ta'lim sohasi kodi",
            "talim_sohasi_nomi": "Ta'lim sohasi nomi",
            "yonalish_kodi": "Yo'nalish kodi",
            "yonalish_nomi": "Yo'nalish nomi",
            "talim_shakli": "Ta'lim shakli",
            "daraja": "Akademik daraja",
            "talabalar_soni": "Talabalar soni",
            "guruhlar_soni": "Guruhlar soni",
            "guruh_prefiksi": "Guruh prefiksi",
        }
