from django.test import TestCase

from accounts.models import Department, Universitet
from plans import dashboard
from plans.dastur.service import dastur_egasimi, dastur_kontekst, dastur_render
from plans.models import SoatTuri, Yuklama
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_guruh,
    make_oqituvchi,
    make_reja,
)


class DasturEgasimiTest(TestCase):
    def setUp(self) -> None:
        self.yil = dashboard.joriy_akademik_yil()
        self.kafedra = Department.objects.create(nomi="Matematika")
        reja = make_reja(boshlanish_yili=self.yil)
        fan = make_fan(reja, kafedra=self.kafedra)
        self.variant = fan.tanlangan_variant
        self.fs = make_fan_semestr(self.variant, semestr=1)
        self.maruza_egasi = make_oqituvchi(kafedra=self.kafedra)
        self.amaliyot_egasi = make_oqituvchi(kafedra=self.kafedra)
        self.begona = make_oqituvchi(kafedra=self.kafedra)
        Yuklama.objects.create(
            fan_semestr=self.fs, tur=SoatTuri.MARUZA, oqituvchi=self.maruza_egasi
        )
        guruh = make_guruh(reja)
        Yuklama.objects.create(
            fan_semestr=self.fs,
            tur=SoatTuri.AMALIYOT,
            oqituvchi=self.amaliyot_egasi,
            guruh=guruh,
        )

    def test_maruza_egasi_ruxsat_etiladi(self) -> None:
        self.assertTrue(dastur_egasimi(self.variant, self.maruza_egasi))

    def test_amaliyot_egasi_rad_etiladi(self) -> None:
        self.assertFalse(dastur_egasimi(self.variant, self.amaliyot_egasi))

    def test_begona_oqituvchi_rad_etiladi(self) -> None:
        self.assertFalse(dastur_egasimi(self.variant, self.begona))


class DasturEgasimiBoshqaYilTest(TestCase):
    """A curriculum whose year isn't "today's" academic year must not block
    its real lecture owner — ownership isn't tied to the calendar."""

    def test_kelajakdagi_reja_egasi_ham_ruxsat_etiladi(self) -> None:
        kafedra = Department.objects.create(nomi="Fizika")
        kelajak_yil = dashboard.joriy_akademik_yil() + 5
        reja = make_reja(yonalish_kodi="60610199", boshlanish_yili=kelajak_yil)
        fan = make_fan(reja, kafedra=kafedra)
        variant = fan.tanlangan_variant
        fs = make_fan_semestr(variant, semestr=1)
        maruza_egasi = make_oqituvchi(kafedra=kafedra)
        Yuklama.objects.create(
            fan_semestr=fs, tur=SoatTuri.MARUZA, oqituvchi=maruza_egasi
        )
        self.assertTrue(dastur_egasimi(variant, maruza_egasi))


class DasturKontekstTest(TestCase):
    def setUp(self) -> None:
        self.yil = dashboard.joriy_akademik_yil()
        Universitet.objects.create(rasmiy_nomi="Test universiteti")
        self.kafedra = Department.objects.create(
            nomi="Matematika", fakultet="Aniq fanlar fakulteti"
        )
        reja = make_reja(boshlanish_yili=self.yil)
        fan = make_fan(reja, raqam="1.05", kafedra=self.kafedra)
        self.variant = fan.tanlangan_variant
        self.fs = make_fan_semestr(self.variant, semestr=1)
        self.maruza_egasi = make_oqituvchi(kafedra=self.kafedra)
        self.amaliyot_egasi = make_oqituvchi(kafedra=self.kafedra)
        Yuklama.objects.create(
            fan_semestr=self.fs, tur=SoatTuri.MARUZA, oqituvchi=self.maruza_egasi
        )
        guruh = make_guruh(reja)
        Yuklama.objects.create(
            fan_semestr=self.fs,
            tur=SoatTuri.AMALIYOT,
            oqituvchi=self.amaliyot_egasi,
            guruh=guruh,
        )

    def test_malumot_maydonlari_toldiriladi(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        self.assertEqual(kontekst["university"], "Test universiteti")
        self.assertEqual(kontekst["faculty"], "Aniq fanlar fakulteti")
        self.assertEqual(kontekst["kafedra"], "Matematika")
        self.assertEqual(kontekst["course"]["code"], self.variant.kodi)
        self.assertEqual(kontekst["course"]["name"], self.variant.nomi)
        self.assertEqual(kontekst["plan_number"], "1.05")
        self.assertEqual(kontekst["total_hours"], self.variant.fan.jami_soat)
        self.assertEqual(kontekst["classroom_total"], self.variant.auditoriya_soat)
        self.assertEqual(kontekst["hours"]["lecture"], self.variant.maruza_soat)
        self.assertEqual(kontekst["semesters_str"], "1")
        self.assertEqual(kontekst["credits_str"], str(self.fs.kredit))

    def test_mualliflar_maruza_egasi_birinchi(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        self.assertEqual(len(kontekst["authors"]), 2)
        self.assertIn(str(self.maruza_egasi.foydalanuvchi), kontekst["authors"][0])

    def test_manba_yoq_maydonlar_bosh(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        self.assertEqual(kontekst["reviewers"], [])
        self.assertEqual(kontekst["purpose"], "")
        self.assertEqual(kontekst["lectures"], [])
        self.assertEqual(kontekst["literature"]["main"], [])

    def test_kengash_maydonlari_bosh_joy(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        self.assertEqual(kontekst["faculty_council"]["number"], "_____")
        self.assertEqual(kontekst["kafedra_council"]["date"], "_____")

    def test_render_hujjat_yaratadi(self) -> None:
        buffer = dastur_render(self.variant)
        self.assertGreater(len(buffer.getvalue()), 0)
