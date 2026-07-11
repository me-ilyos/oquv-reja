from django.test import TestCase
from django.urls import reverse

from accounts.models import Department
from plans.dashboard import joriy_akademik_yil
from plans.models import SoatTuri, Yuklama
from plans.services import guruhlarni_sinxronlash
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_oqituvchi,
    make_reja,
)
from web.tests.helpers import login, mudir_yarat


class KafedraAsosTest(TestCase):
    """Shared fixture: one mudir with a delegated fan-semester in-year."""

    def setUp(self) -> None:
        self.joriy = joriy_akademik_yil()
        self.mudir = mudir_yarat()
        self.kafedra = self.mudir.oqituvchi_profil.kafedra
        self.oqituvchi = make_oqituvchi(kafedra=self.kafedra)
        self.reja = make_reja(boshlanish_yili=self.joriy)
        self.guruhlar = guruhlarni_sinxronlash(self.reja)
        self.fan = make_fan(self.reja, kafedra=self.kafedra)
        self.fs = make_fan_semestr(
            self.fan.tanlangan_variant, semestr=1, kurs_ishi_bor=True
        )
        login(self.client, self.mudir)


class KafedraDashboardTests(KafedraAsosTest):
    def test_oz_fanlari_korinadi(self) -> None:
        javob = self.client.get(reverse("kafedra:dashboard"))
        self.assertContains(javob, "Dasturlashga kirish")
        self.assertContains(javob, "Taqsimlash")

    def test_begona_fan_korinmaydi(self) -> None:
        begona_kafedra = Department.objects.create(nomi="Begona")
        begona = make_fan(self.reja, raqam="1.99", kafedra=begona_kafedra)
        make_fan_semestr(begona.tanlangan_variant, semestr=1, maruza_soat=99)
        javob = self.client.get(reverse("kafedra:dashboard"))
        self.assertEqual(
            [s.fan_semestr.pk for s in javob.context["fs_satrlar"]], [self.fs.pk]
        )


class TaqsimotPanelTests(KafedraAsosTest):
    def test_panel_ochiladi(self) -> None:
        javob = self.client.get(reverse("kafedra:taqsimot_panel", args=[self.fs.pk]))
        self.assertContains(javob, "taqsimoti")
        self.assertContains(javob, "Ma&#x27;ruza")
        self.assertContains(javob, self.guruhlar[0].nomi)

    def test_begona_fs_404(self) -> None:
        begona_kafedra = Department.objects.create(nomi="Begona")
        begona = make_fan(self.reja, raqam="1.99", kafedra=begona_kafedra)
        begona_fs = make_fan_semestr(begona.tanlangan_variant, semestr=1)
        javob = self.client.get(reverse("kafedra:taqsimot_panel", args=[begona_fs.pk]))
        self.assertEqual(javob.status_code, 404)


class YuklamaYaratishTests(KafedraAsosTest):
    def test_maruza_yaratiladi(self) -> None:
        javob = self.client.post(
            reverse("kafedra:maruza_yaratish", args=[self.fs.pk]),
            {"oqituvchi": self.oqituvchi.pk},
        )
        yuklama = Yuklama.objects.get(fan_semestr=self.fs, tur=SoatTuri.MARUZA)
        self.assertEqual(yuklama.soat, 24)
        self.assertContains(javob, 'hx-swap-oob="true"')

    def test_guruh_yuklamasi_yaratiladi(self) -> None:
        self.client.post(
            reverse("kafedra:guruh_yaratish", args=[self.fs.pk]),
            {
                "oqituvchi": self.oqituvchi.pk,
                "guruh": self.guruhlar[0].pk,
                "tur": SoatTuri.AMALIYOT,
            },
        )
        yuklama = Yuklama.objects.get(fan_semestr=self.fs, tur=SoatTuri.AMALIYOT)
        self.assertEqual(yuklama.guruh, self.guruhlar[0])
        self.assertEqual(yuklama.soat, 24)

    def test_kurs_ishi_yaratiladi(self) -> None:
        self.client.post(
            reverse("kafedra:kurs_ishi_yaratish", args=[self.fs.pk]),
            {"oqituvchi": self.oqituvchi.pk, "talabalar_soni": 30},
        )
        yuklama = Yuklama.objects.get(fan_semestr=self.fs, tur=SoatTuri.KURS_ISHI)
        self.assertEqual(yuklama.soat, 60)

    def test_takroriy_guruh_sloti_xato(self) -> None:
        Yuklama.objects.create(
            fan_semestr=self.fs,
            tur=SoatTuri.AMALIYOT,
            oqituvchi=self.oqituvchi,
            guruh=self.guruhlar[0],
        )
        javob = self.client.post(
            reverse("kafedra:guruh_yaratish", args=[self.fs.pk]),
            {
                "oqituvchi": self.oqituvchi.pk,
                "guruh": self.guruhlar[0].pk,
                "tur": SoatTuri.AMALIYOT,
            },
        )
        self.assertEqual(Yuklama.objects.filter(tur=SoatTuri.AMALIYOT).count(), 1)
        self.assertContains(javob, "form-errors")

    def test_sigim_oshsa_xato(self) -> None:
        javob = self.client.post(
            reverse("kafedra:kurs_ishi_yaratish", args=[self.fs.pk]),
            {"oqituvchi": self.oqituvchi.pk, "talabalar_soni": 100},
        )
        self.assertFalse(Yuklama.objects.filter(tur=SoatTuri.KURS_ISHI).exists())
        self.assertContains(javob, "form-errors")

    def test_begona_oqituvchi_qabul_qilinmaydi(self) -> None:
        begona = make_oqituvchi(kafedra=Department.objects.create(nomi="Begona"))
        javob = self.client.post(
            reverse("kafedra:maruza_yaratish", args=[self.fs.pk]),
            {"oqituvchi": begona.pk},
        )
        self.assertFalse(Yuklama.objects.filter(tur=SoatTuri.MARUZA).exists())
        self.assertContains(javob, "form-errors")

    def test_begona_fs_404(self) -> None:
        begona_kafedra = Department.objects.create(nomi="Begona")
        begona = make_fan(self.reja, raqam="1.99", kafedra=begona_kafedra)
        begona_fs = make_fan_semestr(begona.tanlangan_variant, semestr=1)
        javob = self.client.post(
            reverse("kafedra:maruza_yaratish", args=[begona_fs.pk]),
            {"oqituvchi": self.oqituvchi.pk},
        )
        self.assertEqual(javob.status_code, 404)


class KafedraOqituvchilarTests(KafedraAsosTest):
    def test_faqat_oz_kafedrasi_royxatda(self) -> None:
        begona = make_oqituvchi(kafedra=Department.objects.create(nomi="Begona"))
        javob = self.client.get(reverse("kafedra:oqituvchi_list"))
        self.assertContains(javob, str(self.oqituvchi))
        self.assertNotContains(javob, str(begona))

    def test_yaratish_oz_kafedrasiga_boglanadi(self) -> None:
        from accounts.models import Foydalanuvchi, OqituvchiTuri

        turi = OqituvchiTuri.objects.first()
        javob = self.client.post(
            reverse("kafedra:oqituvchi_yangi"),
            {
                "telefon": "+998971112233",
                "first_name": "Sanjar",
                "last_name": "Qodirov",
                "turi": turi.pk,
                "parol": "juda-maxfiy-parol-7",
            },
        )
        self.assertRedirects(javob, reverse("kafedra:oqituvchi_list"))
        yangi = Foydalanuvchi.objects.get(telefon="+998971112233")
        self.assertEqual(yangi.oqituvchi_profil.kafedra, self.kafedra)

    def test_begona_oqituvchini_tahrirlay_olmaydi(self) -> None:
        begona = make_oqituvchi(kafedra=Department.objects.create(nomi="Begona"))
        javob = self.client.get(reverse("kafedra:oqituvchi_tahrir", args=[begona.pk]))
        self.assertEqual(javob.status_code, 404)


class HisobotTests(KafedraAsosTest):
    def test_hisobot_jami_soatlar(self) -> None:
        Yuklama.objects.create(
            fan_semestr=self.fs, tur=SoatTuri.MARUZA, oqituvchi=self.oqituvchi
        )
        javob = self.client.get(reverse("kafedra:hisobot"))
        self.assertContains(javob, "yuklama hisoboti")
        self.assertContains(javob, "Kafedra mudiri")
        self.assertEqual(javob.context["jami_yuklama"], 24)


class YuklamaOchirishTests(KafedraAsosTest):
    def test_ochiriladi(self) -> None:
        yuklama = Yuklama.objects.create(
            fan_semestr=self.fs, tur=SoatTuri.MARUZA, oqituvchi=self.oqituvchi
        )
        javob = self.client.post(reverse("kafedra:yuklama_ochirish", args=[yuklama.pk]))
        self.assertFalse(Yuklama.objects.filter(pk=yuklama.pk).exists())
        self.assertEqual(javob.status_code, 200)

    def test_begona_yuklama_404(self) -> None:
        begona_kafedra = Department.objects.create(nomi="Begona")
        begona_oqituvchi = make_oqituvchi(kafedra=begona_kafedra)
        begona_fan = make_fan(self.reja, raqam="1.99", kafedra=begona_kafedra)
        begona_fs = make_fan_semestr(begona_fan.tanlangan_variant, semestr=1)
        yuklama = Yuklama.objects.create(
            fan_semestr=begona_fs, tur=SoatTuri.MARUZA, oqituvchi=begona_oqituvchi
        )
        javob = self.client.post(reverse("kafedra:yuklama_ochirish", args=[yuklama.pk]))
        self.assertEqual(javob.status_code, 404)
        self.assertTrue(Yuklama.objects.filter(pk=yuklama.pk).exists())
