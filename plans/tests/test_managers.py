from django.test import TestCase

from plans.models import Fan, FanSemestr, FanTuri, SoatTuri, Yuklama
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_oqituvchi,
    make_reja,
    make_variant,
)


class FanQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.reja = make_reja()
        cls.birinchi_kurs_fani = make_fan(cls.reja, raqam="1.01")
        make_fan_semestr(cls.birinchi_kurs_fani.tanlangan_variant, semestr=1)
        cls.ikkinchi_kurs_fani = make_fan(cls.reja, raqam="1.02")
        make_fan_semestr(cls.ikkinchi_kurs_fani.tanlangan_variant, semestr=3)
        make_fan_semestr(cls.ikkinchi_kurs_fani.tanlangan_variant, semestr=4)
        cls.tanlov_fan = make_fan(cls.reja, raqam="2.01", turi=FanTuri.TANLOV)
        make_variant(cls.tanlov_fan, nomi="Muqobil fan")

    def test_oquv_yilida_semestr_juftligini_oladi(self) -> None:
        fanlar = Fan.objects.filter(reja=self.reja).oquv_yilida(2)
        self.assertQuerySetEqual(fanlar, [self.ikkinchi_kurs_fani])

    def test_oquv_yilida_takrorlamaydi(self) -> None:
        # Both semesters of study year 2 match; the fan must appear once.
        fanlar = Fan.objects.oquv_yilida(2)
        self.assertEqual(fanlar.count(), 1)

    def test_effektiv_tanlanmaganlarni_chiqarmaydi(self) -> None:
        effektiv = Fan.objects.filter(reja=self.reja).effektiv()
        self.assertNotIn(self.tanlov_fan, effektiv)
        self.assertIn(self.birinchi_kurs_fani, effektiv)

    def test_tanlov_kutilmoqda(self) -> None:
        kutilmoqda = Fan.objects.tanlov_kutilmoqda()
        self.assertQuerySetEqual(kutilmoqda, [self.tanlov_fan])

    def test_tanlangandan_keyin_effektiv_boladi(self) -> None:
        self.tanlov_fan.tanlangan_variant = self.tanlov_fan.variantlar.first()
        self.tanlov_fan.save(update_fields=["tanlangan_variant"])
        self.assertIn(self.tanlov_fan, Fan.objects.effektiv())
        self.assertEqual(Fan.objects.tanlov_kutilmoqda().count(), 0)


class FanSemestrQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.reja_2024 = make_reja(boshlanish_yili=2024)
        cls.reja_2023 = make_reja(
            yonalish_kodi="60610200", yonalish_nomi="AT", boshlanish_yili=2023
        )
        fan_2024 = make_fan(cls.reja_2024)
        cls.fs_2024_s3 = make_fan_semestr(fan_2024.tanlangan_variant, semestr=3)
        fan_2023 = make_fan(cls.reja_2023)
        cls.fs_2023_s3 = make_fan_semestr(fan_2023.tanlangan_variant, semestr=3)
        cls.fs_2023_s5 = make_fan_semestr(fan_2023.tanlangan_variant, semestr=5)
        cls.tanlov = make_fan(cls.reja_2024, raqam="2.01", turi=FanTuri.TANLOV)
        cls.tanlov_fs = make_fan_semestr(cls.tanlov.variantlar.first(), semestr=3)

    def test_akademik_yilda_rejalarni_farqlaydi(self) -> None:
        # 2025/2026: DI2024 is in semester 3-4, AT2023 in semester 5-6.
        natija = set(FanSemestr.objects.akademik_yilda(2025))
        self.assertEqual(natija, {self.fs_2024_s3, self.fs_2023_s5, self.tanlov_fs})

    def test_effektiv_tanlanmagan_variantni_chiqarmaydi(self) -> None:
        effektiv = FanSemestr.objects.effektiv()
        self.assertNotIn(self.tanlov_fs, effektiv)
        self.assertIn(self.fs_2024_s3, effektiv)

    def test_reja_uchun_va_oquv_yilida(self) -> None:
        natija = FanSemestr.objects.reja_uchun(self.reja_2023).oquv_yilida(3)
        self.assertQuerySetEqual(natija, [self.fs_2023_s5])


class YuklamaQuerySetTest(TestCase):
    def test_akademik_yilda_yuklamalarni_filtrlash(self) -> None:
        reja = make_reja(boshlanish_yili=2024)
        fan = make_fan(reja)
        fs_s1 = make_fan_semestr(fan.tanlangan_variant, semestr=1)
        fs_s3 = make_fan_semestr(fan.tanlangan_variant, semestr=3)
        oqituvchi = make_oqituvchi()
        Yuklama.objects.create(
            fan_semestr=fs_s1, tur=SoatTuri.MARUZA, oqituvchi=oqituvchi
        )
        keyingi_yil = Yuklama.objects.create(
            fan_semestr=fs_s3, tur=SoatTuri.MARUZA, oqituvchi=oqituvchi
        )
        self.assertQuerySetEqual(Yuklama.objects.akademik_yilda(2025), [keyingi_yil])
