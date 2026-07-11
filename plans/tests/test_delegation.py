from django.test import TestCase

from plans.dashboard import joriy_akademik_yil
from plans.delegation import fan_semestr_holati, fs_satri, kafedra_fs_satrlari
from plans.models import SoatTuri, Yuklama
from plans.services import guruhlarni_sinxronlash
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_oqituvchi,
    make_reja,
)


class FanSemestrHolatiTests(TestCase):
    def setUp(self) -> None:
        self.reja = make_reja()  # 3 guruh, 75 talaba
        self.guruhlar = guruhlarni_sinxronlash(self.reja)
        self.oqituvchi = make_oqituvchi()
        self.fan = make_fan(self.reja, kafedra=self.oqituvchi.kafedra)
        self.fs = make_fan_semestr(self.fan.tanlangan_variant, kurs_ishi_bor=True)

    def test_shakllar_togri_quriladi(self) -> None:
        holatlar = {h.tur: h for h in fan_semestr_holati(self.fs)}

        self.assertIsNone(holatlar[SoatTuri.MARUZA].maruza_yuklama)
        self.assertEqual(len(holatlar[SoatTuri.AMALIYOT].guruh_slotlar), 3)
        self.assertEqual(holatlar[SoatTuri.AMALIYOT].guruh_soat, 24)
        self.assertEqual(holatlar[SoatTuri.KURS_ISHI].qolgan_talabalar, 75)

    def test_yuklamalar_slotlarga_ulanadi(self) -> None:
        Yuklama.objects.create(
            fan_semestr=self.fs, tur=SoatTuri.MARUZA, oqituvchi=self.oqituvchi
        )
        Yuklama.objects.create(
            fan_semestr=self.fs,
            tur=SoatTuri.AMALIYOT,
            oqituvchi=self.oqituvchi,
            guruh=self.guruhlar[0],
        )
        Yuklama.objects.create(
            fan_semestr=self.fs,
            tur=SoatTuri.KURS_ISHI,
            oqituvchi=self.oqituvchi,
            talabalar_soni=30,
        )

        holatlar = {h.tur: h for h in fan_semestr_holati(self.fs)}

        self.assertIsNotNone(holatlar[SoatTuri.MARUZA].maruza_yuklama)
        band = [s for s in holatlar[SoatTuri.AMALIYOT].guruh_slotlar if s.yuklama]
        self.assertEqual(len(band), 1)
        self.assertEqual(holatlar[SoatTuri.KURS_ISHI].qolgan_talabalar, 45)
        self.assertEqual(holatlar[SoatTuri.KURS_ISHI].taqsimlangan_soat, 60)

    def test_fs_satri_qoldiqni_koradi(self) -> None:
        satr = fs_satri(self.fs)
        self.assertTrue(satr.qoldiq_bor)
        self.assertEqual(satr.turlar[SoatTuri.MARUZA].talab_soat, 24)


class KafedraFsSatrlariTests(TestCase):
    def test_faqat_oz_kafedrasi(self) -> None:
        joriy = joriy_akademik_yil()
        reja = make_reja(boshlanish_yili=joriy)
        oqituvchi = make_oqituvchi()
        bizniki = make_fan(reja, raqam="1.01", kafedra=oqituvchi.kafedra)
        make_fan_semestr(bizniki.tanlangan_variant, semestr=1)
        begona = make_fan(reja, raqam="1.02")
        make_fan_semestr(begona.tanlangan_variant, semestr=1)

        satrlar = kafedra_fs_satrlari(oqituvchi.kafedra, joriy)

        self.assertEqual(len(satrlar), 1)
        self.assertEqual(satrlar[0].fan_semestr.variant.fan_id, bizniki.pk)
