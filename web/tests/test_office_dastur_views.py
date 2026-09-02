from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Department
from plans.dashboard import joriy_akademik_yil
from plans.dastur.topshirish import dastur_rad_etish, dastur_topshirish
from plans.models import SoatTuri, TopshirishHolati, Yuklama
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_oqituvchi,
    make_reja,
)
from web.tests.helpers import login, office_admin_yarat, oqituvchi_yarat


class DasturTopshirishlarViewTests(TestCase):
    def setUp(self) -> None:
        kafedra = Department.objects.create(nomi="Matematika")
        reja = make_reja(boshlanish_yili=joriy_akademik_yil())
        fan = make_fan(reja, kafedra=kafedra)
        self.variant = fan.tanlangan_variant
        fs = make_fan_semestr(self.variant, semestr=1)
        self.egasi = make_oqituvchi(kafedra=kafedra)
        Yuklama.objects.create(
            fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=self.egasi
        )
        self.topshirish = dastur_topshirish(
            self.variant, self.egasi, SimpleUploadedFile("d.docx", b"mazmun")
        )

    def test_oqituvchi_kira_olmaydi(self) -> None:
        login(self.client, oqituvchi_yarat())
        javob = self.client.get(reverse("office:dastur_topshirishlar"))
        self.assertEqual(javob.status_code, 302)

    def test_admin_royxatni_koradi(self) -> None:
        login(self.client, office_admin_yarat())
        javob = self.client.get(reverse("office:dastur_topshirishlar"))
        self.assertContains(javob, self.egasi.foydalanuvchi.first_name)

    def test_royxat_bir_variant_uchun_bitta_qator(self) -> None:
        admin = office_admin_yarat()
        dastur_rad_etish(self.topshirish, admin, "To'liq emas")
        dastur_rad_etish(
            dastur_topshirish(
                self.variant, self.egasi, SimpleUploadedFile("v2.docx", b"m")
            ),
            admin,
            "Yana kamchilik bor",
        )
        uchinchi = dastur_topshirish(
            self.variant, self.egasi, SimpleUploadedFile("v3.docx", b"m")
        )

        login(self.client, admin)
        javob = self.client.get(reverse("office:dastur_topshirishlar"))

        self.assertEqual(len(javob.context["topshirishlar"]), 1)
        self.assertEqual(javob.context["topshirishlar"][0].pk, uchinchi.pk)

    def test_qabul_qilish(self) -> None:
        login(self.client, office_admin_yarat())
        javob = self.client.post(
            reverse("office:dastur_qabul", args=[self.topshirish.pk])
        )
        self.assertEqual(javob.status_code, 200)
        self.topshirish.refresh_from_db()
        self.assertEqual(self.topshirish.holat, TopshirishHolati.QABUL_QILINDI)

    def test_rad_etish(self) -> None:
        login(self.client, office_admin_yarat())
        javob = self.client.post(
            reverse("office:dastur_rad", args=[self.topshirish.pk]),
            {"izoh": "Mavzular yetarli emas"},
        )
        self.assertEqual(javob.status_code, 200)
        self.topshirish.refresh_from_db()
        self.assertEqual(self.topshirish.holat, TopshirishHolati.RAD_ETILDI)
        self.assertEqual(self.topshirish.izoh, "Mavzular yetarli emas")

    def test_fayl_yuklab_olinadi(self) -> None:
        login(self.client, office_admin_yarat())
        javob = self.client.get(
            reverse("office:dastur_fayl", args=[self.topshirish.pk])
        )
        self.assertEqual(javob.status_code, 200)


class DasturTarixiViewTests(TestCase):
    def setUp(self) -> None:
        kafedra = Department.objects.create(nomi="Biologiya")
        reja = make_reja(yonalish_kodi="60610144", boshlanish_yili=joriy_akademik_yil())
        fan = make_fan(reja, kafedra=kafedra)
        self.variant = fan.tanlangan_variant
        fs = make_fan_semestr(self.variant, semestr=1)
        self.egasi = make_oqituvchi(kafedra=kafedra)
        Yuklama.objects.create(
            fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=self.egasi
        )
        self.admin = office_admin_yarat()
        birinchi = dastur_topshirish(
            self.variant, self.egasi, SimpleUploadedFile("v1.docx", b"m")
        )
        dastur_rad_etish(birinchi, self.admin, "Mavzular yetarli emas")
        dastur_topshirish(self.variant, self.egasi, SimpleUploadedFile("v2.docx", b"m"))
        self.url = reverse("office:dastur_tarixi", args=[self.variant.pk])

    def test_barcha_urinishlar_korsatiladi(self) -> None:
        login(self.client, self.admin)
        javob = self.client.get(self.url)
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "1-urinish")
        self.assertContains(javob, "2-urinish")
        self.assertContains(javob, "Mavzular yetarli emas")
