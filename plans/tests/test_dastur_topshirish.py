from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import Department
from plans import dashboard
from plans.dastur.topshirish import (
    dastur_qabul_qilish,
    dastur_rad_etish,
    dastur_topshirish,
)
from plans.models import DasturTopshirish, SoatTuri, TopshirishHolati, Yuklama
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_oqituvchi,
    make_reja,
)
from web.tests.helpers import office_admin_yarat


def _fayl(nomi: str = "dastur.docx") -> SimpleUploadedFile:
    return SimpleUploadedFile(nomi, b"mazmun", content_type="application/octet-stream")


class DasturTopshirishTest(TestCase):
    def setUp(self) -> None:
        yil = dashboard.joriy_akademik_yil()
        kafedra = Department.objects.create(nomi="Matematika")
        reja = make_reja(boshlanish_yili=yil)
        fan = make_fan(reja, kafedra=kafedra)
        self.variant = fan.tanlangan_variant
        fs = make_fan_semestr(self.variant, semestr=1)
        self.egasi = make_oqituvchi(kafedra=kafedra)
        self.begona = make_oqituvchi(kafedra=kafedra)
        Yuklama.objects.create(
            fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=self.egasi
        )

    def test_egasi_topshiradi(self) -> None:
        topshirish = dastur_topshirish(self.variant, self.egasi, _fayl())
        self.assertEqual(topshirish.holat, TopshirishHolati.KUTILMOQDA)
        self.assertEqual(topshirish.oqituvchi, self.egasi)

    def test_begona_topshira_olmaydi(self) -> None:
        with self.assertRaises(ValidationError):
            dastur_topshirish(self.variant, self.begona, _fayl())

    def test_qayta_topshirish_holatni_tiklaydi(self) -> None:
        birinchi = dastur_topshirish(self.variant, self.egasi, _fayl("v1.docx"))
        dastur_rad_etish(birinchi, office_admin_yarat(), "To'liq emas")
        eski_fayl_nomi = birinchi.fayl.name

        ikkinchi = dastur_topshirish(self.variant, self.egasi, _fayl("v2.docx"))

        self.assertEqual(DasturTopshirish.objects.count(), 1)
        self.assertEqual(ikkinchi.holat, TopshirishHolati.KUTILMOQDA)
        self.assertEqual(ikkinchi.izoh, "")
        self.assertIsNone(ikkinchi.korib_chiqqan)
        self.assertNotIn(eski_fayl_nomi, DasturTopshirish.objects.get().fayl.name)


class DasturQabulRadTest(TestCase):
    def setUp(self) -> None:
        yil = dashboard.joriy_akademik_yil()
        kafedra = Department.objects.create(nomi="Fizika")
        reja = make_reja(yonalish_kodi="60610199", boshlanish_yili=yil)
        fan = make_fan(reja, kafedra=kafedra)
        variant = fan.tanlangan_variant
        fs = make_fan_semestr(variant, semestr=1)
        self.egasi = make_oqituvchi(kafedra=kafedra)
        Yuklama.objects.create(
            fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=self.egasi
        )
        self.topshirish = dastur_topshirish(variant, self.egasi, _fayl())
        self.admin = office_admin_yarat()

    def test_qabul_qilish(self) -> None:
        dastur_qabul_qilish(self.topshirish, self.admin)
        self.topshirish.refresh_from_db()
        self.assertEqual(self.topshirish.holat, TopshirishHolati.QABUL_QILINDI)
        self.assertEqual(self.topshirish.korib_chiqqan, self.admin)
        self.assertIsNotNone(self.topshirish.korib_chiqilgan_vaqt)

    def test_rad_etish_izoh_bilan(self) -> None:
        dastur_rad_etish(self.topshirish, self.admin, "Mavzular yetarli emas")
        self.topshirish.refresh_from_db()
        self.assertEqual(self.topshirish.holat, TopshirishHolati.RAD_ETILDI)
        self.assertEqual(self.topshirish.izoh, "Mavzular yetarli emas")

    def test_rad_etish_izohsiz_xato(self) -> None:
        with self.assertRaises(ValidationError):
            dastur_rad_etish(self.topshirish, self.admin, "  ")
