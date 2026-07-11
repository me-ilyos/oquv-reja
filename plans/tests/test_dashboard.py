from datetime import date

from django.test import TestCase

from accounts.models import Department
from plans.dashboard import (
    jami_talabalar,
    joriy_akademik_yil,
    kafedra_qamrovi,
    ofis_fan_satrlari,
    statlarni_hisoblash,
    tanlanadigan_yillar,
)
from plans.models import FanTuri, SoatTuri, Yuklama
from plans.services import ofis_taqsimoti
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_guruh,
    make_oqituvchi,
    make_reja,
    make_variant,
)


class JoriyAkademikYilTests(TestCase):
    def test_sentyabrgacha_oldingi_yil(self) -> None:
        self.assertEqual(joriy_akademik_yil(date(2026, 7, 11)), 2025)

    def test_sentyabrdan_boshlab_joriy_yil(self) -> None:
        self.assertEqual(joriy_akademik_yil(date(2026, 9, 1)), 2026)


class TanlanadiganYillarTests(TestCase):
    def test_otgan_yillar_chiqmaydi(self) -> None:
        joriy = joriy_akademik_yil()
        reja = make_reja(boshlanish_yili=joriy - 1)
        fan = make_fan(reja)
        # Semestr 1-2 -> o'tgan yil; semestr 3-4 -> joriy yil (takrorsiz).
        make_fan_semestr(fan.tanlangan_variant, semestr=1)
        make_fan_semestr(fan.tanlangan_variant, semestr=3)
        make_fan_semestr(fan.tanlangan_variant, semestr=4)
        self.assertEqual(tanlanadigan_yillar(), [joriy])

    def test_tanlanmagan_tanlov_yili_ham_chiqadi(self) -> None:
        joriy = joriy_akademik_yil()
        reja = make_reja(boshlanish_yili=joriy)
        fan = make_fan(reja, turi=FanTuri.TANLOV)
        make_fan_semestr(fan.variantlar.first(), semestr=1)
        self.assertEqual(tanlanadigan_yillar(), [joriy])


class StatlarTests(TestCase):
    def setUp(self) -> None:
        self.joriy = joriy_akademik_yil()
        self.reja = make_reja(boshlanish_yili=self.joriy)
        self.kafedra = Department.objects.create(nomi="Tarix")

    def test_kafedra_boyicha_taqsimlanadi(self) -> None:
        biriktirilgan = make_fan(self.reja, raqam="1.01", kafedra=self.kafedra)
        make_fan_semestr(biriktirilgan.tanlangan_variant, semestr=1)
        ochiq = make_fan(self.reja, raqam="1.02")
        make_fan_semestr(ochiq.tanlangan_variant, semestr=1)

        stat = statlarni_hisoblash(ofis_taqsimoti(self.joriy))

        # Har fan-semestr: 24 ma'ruza + (24 amaliyot + 24 lab) x 3 guruh = 168.
        self.assertEqual(stat.jami_soat, 336)
        self.assertEqual(stat.kafedraga_biriktirilgan_soat, 168)
        self.assertEqual(stat.kafedraga_biriktirilmagan_soat, 168)
        self.assertEqual(stat.tur_soatlari[SoatTuri.MARUZA], 48)
        self.assertEqual(stat.oqituvchiga_taqsimlangan_soat, 0)
        self.assertEqual(stat.taqsimlanmagan_soat, 336)

    def test_yuklama_taqsimlanganini_kamaytiradi(self) -> None:
        fan = make_fan(self.reja, kafedra=self.kafedra)
        fs = make_fan_semestr(fan.tanlangan_variant, semestr=1)
        oqituvchi = make_oqituvchi(kafedra=self.kafedra)
        Yuklama.objects.create(fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=oqituvchi)

        stat = statlarni_hisoblash(ofis_taqsimoti(self.joriy))

        self.assertEqual(stat.oqituvchiga_taqsimlangan_soat, 24)
        self.assertEqual(stat.taqsimlanmagan_soat, 168 - 24)

    def test_soni_kiritilmagan_nomalum(self) -> None:
        reja = make_reja(
            yonalish_kodi="60610199",
            boshlanish_yili=self.joriy,
            talabalar_soni=None,
            guruhlar_soni=None,
        )
        fan = make_fan(reja)
        make_fan_semestr(fan.tanlangan_variant, semestr=1)

        stat = statlarni_hisoblash(ofis_taqsimoti(self.joriy))

        # Amaliyot va laboratoriya talabi guruhlar sonisiz noma'lum.
        self.assertEqual(stat.nomalum_talab_soni, 2)
        self.assertEqual(stat.jami_soat, 24)


class FanSatrlariTests(TestCase):
    def setUp(self) -> None:
        self.joriy = joriy_akademik_yil()
        self.reja = make_reja(boshlanish_yili=self.joriy)

    def test_ikki_semestr_bitta_qatorga_yigiladi(self) -> None:
        fan = make_fan(self.reja)
        make_fan_semestr(fan.tanlangan_variant, semestr=1)
        make_fan_semestr(fan.tanlangan_variant, semestr=2)

        satrlar = ofis_fan_satrlari(self.joriy)

        self.assertEqual(len(satrlar), 1)
        self.assertEqual(satrlar[0].tur_soatlari[SoatTuri.MARUZA], 48)
        self.assertEqual(len(satrlar[0].fan_semestrlar), 2)

    def test_tanlanmagan_tanlov_belgilanadi(self) -> None:
        fan = make_fan(self.reja, raqam="2.01", turi=FanTuri.TANLOV)
        make_fan_semestr(fan.variantlar.first(), semestr=1)
        make_variant(fan, nomi="Muqobil fan")

        satrlar = ofis_fan_satrlari(self.joriy)

        self.assertEqual(len(satrlar), 1)
        self.assertTrue(satrlar[0].tanlanmagan)
        self.assertTrue(satrlar[0].biriktirilmagan)

    def test_otgan_yil_semestri_chiqmaydi(self) -> None:
        reja = make_reja(yonalish_kodi="60610188", boshlanish_yili=self.joriy - 1)
        fan = make_fan(reja)
        make_fan_semestr(fan.tanlangan_variant, semestr=1)

        self.assertEqual(ofis_fan_satrlari(self.joriy), [])


class JamiTalabalarTests(TestCase):
    def test_yilda_qatnashgan_rejalar_yigiladi(self) -> None:
        joriy = joriy_akademik_yil()
        reja1 = make_reja(boshlanish_yili=joriy, talabalar_soni=75)
        fan1 = make_fan(reja1)
        make_fan_semestr(fan1.tanlangan_variant, semestr=1)
        reja2 = make_reja(
            yonalish_kodi="60610177", boshlanish_yili=joriy - 1, talabalar_soni=50
        )
        fan2 = make_fan(reja2)
        make_fan_semestr(fan2.tanlangan_variant, semestr=3)

        self.assertEqual(jami_talabalar(joriy), 125)


class KafedraQamroviTests(TestCase):
    def test_qamrov_hisoblanadi(self) -> None:
        joriy = joriy_akademik_yil()
        reja = make_reja(boshlanish_yili=joriy)
        kafedra = Department.objects.create(nomi="Fizika")
        fan = make_fan(reja, kafedra=kafedra)
        fs = make_fan_semestr(fan.tanlangan_variant, semestr=1)
        oqituvchi = make_oqituvchi(kafedra=kafedra)
        make_guruh(reja)
        Yuklama.objects.create(fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=oqituvchi)

        qamrov = {q.kafedra.nomi: q for q in kafedra_qamrovi(joriy)}

        self.assertEqual(qamrov["Fizika"].biriktirilgan_soat, 168)
        self.assertEqual(qamrov["Fizika"].taqsimlangan_soat, 24)
        self.assertEqual(qamrov["Fizika"].oqituvchilar_soni, 1)
