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
from web.tests.helpers import foydalanuvchi_yarat, login


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
