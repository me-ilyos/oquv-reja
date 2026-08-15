from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol
from plans.dashboard import joriy_akademik_yil
from plans.models import SoatTuri, Yuklama
from plans.services import oqituvchi_yillik_yuklamasi
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_oqituvchi,
    make_reja,
)
from web.tests.helpers import foydalanuvchi_yarat, login, mudir_yarat


class MenYuklamalarimTests(TestCase):
    def setUp(self) -> None:
        self.joriy = joriy_akademik_yil()
        self.profil = make_oqituvchi()
        self.reja = make_reja(boshlanish_yili=self.joriy)
        fan = make_fan(self.reja, kafedra=self.profil.kafedra)
        self.fs = make_fan_semestr(fan.tanlangan_variant, semestr=1)
        login(self.client, self.profil.foydalanuvchi)

    def test_faqat_oz_yuklamalari(self) -> None:
        boshqa = make_oqituvchi(kafedra=self.profil.kafedra)
        Yuklama.objects.create(
            fan_semestr=self.fs, tur=SoatTuri.MARUZA, oqituvchi=self.profil
        )
        Yuklama.objects.create(
            fan_semestr=self.fs,
            tur=SoatTuri.KURS_ISHI,
            oqituvchi=boshqa,
            talabalar_soni=10,
        )
        javob = self.client.get(reverse("men:yuklamalar"))
        self.assertEqual(len(javob.context["yuklamalar"]), 1)
        self.assertEqual(javob.context["yuklamalar"][0].tur, SoatTuri.MARUZA)

    def test_jami_soat_servis_bilan_mos(self) -> None:
        Yuklama.objects.create(
            fan_semestr=self.fs, tur=SoatTuri.MARUZA, oqituvchi=self.profil
        )
        javob = self.client.get(reverse("men:yuklamalar"))
        self.assertEqual(
            javob.context["jami_soat"],
            oqituvchi_yillik_yuklamasi(self.profil, self.joriy),
        )
        self.assertContains(javob, "Jami yuklama soat")

    def test_otgan_yil_yuklamasi_korinmaydi(self) -> None:
        eski_reja = make_reja(yonalish_kodi="60610155", boshlanish_yili=self.joriy - 2)
        eski_fan = make_fan(eski_reja, kafedra=self.profil.kafedra)
        eski_fs = make_fan_semestr(eski_fan.tanlangan_variant, semestr=1)
        Yuklama.objects.create(
            fan_semestr=eski_fs, tur=SoatTuri.MARUZA, oqituvchi=self.profil
        )
        javob = self.client.get(reverse("men:yuklamalar"))
        self.assertEqual(len(javob.context["yuklamalar"]), 0)

    def test_profilsiz_oqituvchi_bosh_holat(self) -> None:
        login(self.client, foydalanuvchi_yarat(Rol.TEACHER))
        javob = self.client.get(reverse("men:yuklamalar"))
        self.assertContains(javob, "Profil biriktirilmagan")

    def test_kafedra_mudiri_oz_yuklamasini_koradi(self) -> None:
        mudir = mudir_yarat()
        profil = mudir.oqituvchi_profil
        reja = make_reja(yonalish_kodi="60610177", boshlanish_yili=self.joriy)
        fan = make_fan(reja, kafedra=profil.kafedra)
        fs = make_fan_semestr(fan.tanlangan_variant, semestr=1)
        Yuklama.objects.create(fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=profil)
        login(self.client, mudir)
        javob = self.client.get(reverse("men:yuklamalar"))
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(javob.context["yuklamalar"]), 1)


class MenOquvDasturTests(TestCase):
    def setUp(self) -> None:
        self.joriy = joriy_akademik_yil()
        self.maruza_egasi = make_oqituvchi()
        reja = make_reja(boshlanish_yili=self.joriy)
        fan = make_fan(reja, kafedra=self.maruza_egasi.kafedra)
        self.variant = fan.tanlangan_variant
        fs = make_fan_semestr(self.variant, semestr=1)
        Yuklama.objects.create(
            fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=self.maruza_egasi
        )
        self.url = reverse("men:dastur", args=[self.variant.pk])

    def test_maruza_egasi_hujjatni_yuklab_oladi(self) -> None:
        login(self.client, self.maruza_egasi.foydalanuvchi)
        javob = self.client.get(self.url)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(
            javob["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def test_begona_oqituvchi_rad_etiladi(self) -> None:
        begona = make_oqituvchi(kafedra=self.maruza_egasi.kafedra)
        login(self.client, begona.foydalanuvchi)
        javob = self.client.get(self.url)
        self.assertEqual(javob.status_code, 403)

    def test_tizimga_kirmagan_foydalanuvchi_qaytariladi(self) -> None:
        javob = self.client.get(self.url)
        self.assertEqual(javob.status_code, 302)

    def test_kafedra_mudiri_ham_ozi_oqigan_dasturni_yaratadi(self) -> None:
        mudir = mudir_yarat()
        profil = mudir.oqituvchi_profil
        reja = make_reja(yonalish_kodi="60610188", boshlanish_yili=self.joriy)
        fan = make_fan(reja, kafedra=profil.kafedra)
        variant = fan.tanlangan_variant
        fs = make_fan_semestr(variant, semestr=1)
        Yuklama.objects.create(fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=profil)
        login(self.client, mudir)
        javob = self.client.get(reverse("men:dastur", args=[variant.pk]))
        self.assertEqual(javob.status_code, 200)
