"""Forms for creating (via Excel upload) and correcting an o'quv reja."""

from django import forms

from plans.models import OquvReja
from plans.uploads import YuklashParametrlari


class RejaImportForm(forms.Form):
    fayl = forms.FileField(
        label="Excel fayl (.xlsx)",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
    )
    bilim_sohasi_kodi = forms.CharField(label="Bilim sohasi kodi", max_length=10)
    bilim_sohasi_nomi = forms.CharField(label="Bilim sohasi nomi", max_length=255)
    talim_sohasi_kodi = forms.CharField(label="Ta'lim sohasi kodi", max_length=10)
    talim_sohasi_nomi = forms.CharField(label="Ta'lim sohasi nomi", max_length=255)
    boshlanish_yili = forms.IntegerField(
        label="Boshlanish yili",
        required=False,
        min_value=2000,
        max_value=2100,
        help_text="Bo'sh qoldirilsa fayldan o'qiladi",
    )
    yonalish_kodi = forms.CharField(
        label="Yo'nalish kodi",
        required=False,
        max_length=20,
        help_text="Bo'sh qoldirilsa fayldan o'qiladi",
    )
    yonalish_nomi = forms.CharField(
        label="Yo'nalish nomi",
        required=False,
        max_length=255,
        help_text="Bo'sh qoldirilsa fayldan o'qiladi",
    )
    talim_shakli = forms.CharField(
        label="Ta'lim shakli",
        required=False,
        max_length=100,
        help_text="Bo'sh qoldirilsa fayldan o'qiladi",
    )
    daraja = forms.CharField(
        label="Akademik daraja",
        required=False,
        max_length=100,
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
            bilim_sohasi_kodi=self.cleaned_data["bilim_sohasi_kodi"],
            bilim_sohasi_nomi=self.cleaned_data["bilim_sohasi_nomi"],
            talim_sohasi_kodi=self.cleaned_data["talim_sohasi_kodi"],
            talim_sohasi_nomi=self.cleaned_data["talim_sohasi_nomi"],
            talabalar_soni=self.cleaned_data["talabalar_soni"],
            guruhlar_soni=self.cleaned_data["guruhlar_soni"],
            guruh_prefiksi=self.cleaned_data["guruh_prefiksi"],
            boshlanish_yili=self.cleaned_data["boshlanish_yili"],
            replace=self.cleaned_data["replace"],
            yonalish_kodi=self.cleaned_data["yonalish_kodi"],
            yonalish_nomi=self.cleaned_data["yonalish_nomi"],
            talim_shakli=self.cleaned_data["talim_shakli"],
            daraja=self.cleaned_data["daraja"],
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
