from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Department
from plans.models import FanTuri
from plans.tests.factories import make_fan, make_fan_semestr, make_reja
from web.tests.helpers import login, office_admin_yarat


class RejaListTests(TestCase):
    def setUp(self) -> None:
        login(self.client, office_admin_yarat())

    def test_rejalar_royxati(self) -> None:
        make_reja()
        javob = self.client.get(reverse("office:reja_list"))
        self.assertContains(javob, "Dasturiy injiniring")


class RejaImportTests(TestCase):
    def setUp(self) -> None:
        login(self.client, office_admin_yarat())

    def test_notogri_fayl_xato_korsatadi(self) -> None:
        javob = self.client.post(
            reverse("office:reja_yangi"),
            {
                "fayl": SimpleUploadedFile("reja.xlsx", b"bu excel emas"),
                "talabalar_soni": 50,
                "guruhlar_soni": 2,
                "guruh_prefiksi": "BH",
            },
        )
        self.assertContains(javob, "xlsx formatida emas")


class RejaDetailTests(TestCase):
    def setUp(self) -> None:
        self.reja = make_reja()
        login(self.client, office_admin_yarat())

    def test_semestrovka_chiplari(self) -> None:
        fan = make_fan(self.reja)
        make_fan_semestr(fan.tanlangan_variant, semestr=1, haftalik_soat=6)
        javob = self.client.get(reverse("office:reja_detail", args=[self.reja.pk]))
        self.assertContains(javob, "sem-fill")
        self.assertContains(javob, "Majburiy fanlar")
        self.assertContains(javob, "Dasturlashga kirish")

    def test_tanlanmagan_tanlov_belgisi(self) -> None:
        fan = make_fan(self.reja, raqam="2.01", turi=FanTuri.TANLOV)
        make_fan_semestr(fan.variantlar.first(), semestr=1)
        javob = self.client.get(reverse("office:reja_detail", args=[self.reja.pk]))
        self.assertContains(javob, "TANLANMAGAN")

    def test_detaldan_kafedra_biriktirish_redirect(self) -> None:
        kafedra = Department.objects.create(nomi="Iqtisod")
        fan = make_fan(self.reja)
        make_fan_semestr(fan.tanlangan_variant, semestr=1)
        variant = fan.tanlangan_variant
        javob = self.client.post(
            reverse("office:kafedra_biriktirish", args=[variant.pk]),
            {
                "kafedra": kafedra.pk,
                "redirect": reverse("office:reja_detail", args=[self.reja.pk]),
            },
        )
        self.assertRedirects(javob, reverse("office:reja_detail", args=[self.reja.pk]))
        variant.refresh_from_db()
        self.assertEqual(variant.kafedra, kafedra)


class RejaTahrirTests(TestCase):
    def setUp(self) -> None:
        self.reja = make_reja(guruhlar_soni=2)
        login(self.client, office_admin_yarat())

    def test_guruhlar_soni_oshirilsa_guruhlar_yaratiladi(self) -> None:
        javob = self.client.post(
            reverse("office:reja_tahrir", args=[self.reja.pk]),
            {
                "yonalish_nomi": self.reja.yonalish_nomi,
                "talabalar_soni": 90,
                "guruhlar_soni": 3,
                "guruh_prefiksi": "DI",
            },
        )
        self.assertRedirects(javob, reverse("office:reja_detail", args=[self.reja.pk]))
        self.reja.refresh_from_db()
        self.assertEqual(self.reja.guruhlar.count(), 3)
