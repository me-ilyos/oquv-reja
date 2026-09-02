from django.test import TestCase
from docx.oxml.ns import qn

from accounts.models import Department, Universitet
from plans import dashboard
from plans.dastur.kontekst import dastur_kontekst
from plans.dastur.mavzular import bosh_mavzular
from plans.dastur.service import dastur_egasimi, dastur_render
from plans.models import SoatTuri, Yuklama
from plans.tests.factories import (
    make_fan,
    make_fan_semestr,
    make_guruh,
    make_oqituvchi,
    make_reja,
)


class BoshMavzularTest(TestCase):
    def test_soat_ikkiga_bolinadi(self) -> None:
        mavzular = bosh_mavzular(32, "M")
        self.assertEqual(len(mavzular), 16)
        self.assertEqual(mavzular[0].code, "M1")
        self.assertEqual(mavzular[-1].code, "M16")
        self.assertTrue(all(m.hours == 2 and m.title == "" for m in mavzular))

    def test_toq_soat_qoldiq_qatori(self) -> None:
        mavzular = bosh_mavzular(5, "A")
        self.assertEqual([m.hours for m in mavzular], [2, 2, 1])
        self.assertEqual(mavzular[-1].code, "A3")

    def test_nol_soat_bosh_royxat(self) -> None:
        self.assertEqual(bosh_mavzular(0, "L"), [])
        self.assertEqual(bosh_mavzular(-4, "S"), [])


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
        reja = make_reja(
            boshlanish_yili=self.yil,
            bilim_sohasi_kodi="600000",
            bilim_sohasi_nomi="Aniq fanlar",
        )
        fan = make_fan(reja, raqam="1.05", kafedra=self.kafedra, jami_soat=120)
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
        self.assertEqual(kontekst["kafedra"], "Matematika")
        self.assertEqual(kontekst["course"]["code"], self.variant.kodi)
        self.assertEqual(kontekst["course"]["name"], self.variant.nomi)
        self.assertEqual(
            kontekst["plan_number"], f"{self.variant.fan.reja.yonalish_kodi}-1.05"
        )
        self.assertEqual(kontekst["major"]["bilim_sohasi"], "600000 – Aniq fanlar")
        self.assertEqual(kontekst["total_hours"], str(self.variant.fan.jami_soat))
        self.assertEqual(kontekst["classroom_total"], str(self.variant.auditoriya_soat))
        self.assertEqual(kontekst["hours"]["lecture"], str(self.variant.maruza_soat))
        self.assertEqual(kontekst["semesters_str"], "1")
        self.assertEqual(kontekst["credits_str"], str(self.fs.kredit))

    def test_nol_soat_chiziqcha_bilan_korsatiladi(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        self.assertEqual(kontekst["hours"]["seminar"], "-")
        self.assertEqual(kontekst["hours"]["coursework"], "-")

    def test_mustaqil_talim_hisoblanadi(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        kutilgan = self.variant.fan.jami_soat - self.variant.auditoriya_soat
        self.assertEqual(kontekst["hours"]["self_study"], str(kutilgan))

    def test_mavzular_soatdan_hisoblanadi(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        self.assertEqual(len(kontekst["lectures"]), self.variant.maruza_soat // 2)
        self.assertEqual(kontekst["practicals"][0].code, "A1")
        self.assertEqual(len(kontekst["labs"]), self.variant.laboratoriya_soat // 2)
        self.assertEqual(kontekst["seminars"], [])

    def test_kop_semestrli_oquv_yillari_takrorlanmaydi(self) -> None:
        make_fan_semestr(self.variant, semestr=2)
        kontekst = dastur_kontekst(self.variant)
        boshlanish = self.variant.fan.reja.boshlanish_yili
        self.assertEqual(
            kontekst["academic_years_str"], f"{boshlanish}/{boshlanish + 1}"
        )

    def test_kengash_maydonlari_bosh_joy(self) -> None:
        kontekst = dastur_kontekst(self.variant)
        self.assertEqual(kontekst["kafedra_council"]["date"], "_____")

    def test_render_hujjat_yaratadi(self) -> None:
        buffer = dastur_render(self.variant)
        self.assertGreater(len(buffer.getvalue()), 0)

    def test_render_mavzu_qatorlari_hujjatga_kiradi(self) -> None:
        from docx import Document

        buffer = dastur_render(self.variant)
        hujjat = Document(buffer)
        matn = "\n".join(
            cell.text
            for table in hujjat.tables
            for row in table.rows
            for cell in row.cells
        )
        self.assertIn("M1", matn)
        self.assertIn(f"M{self.variant.maruza_soat // 2}", matn)

    def test_muqova_teglari_toldiriladi(self) -> None:
        from docx import Document

        buffer = dastur_render(self.variant)
        hujjat = Document(buffer)
        muqova_matni = "\n".join(p.text for p in hujjat.paragraphs)
        self.assertNotRegex(muqova_matni, r"\{\{|\{%tr")
        self.assertIn(self.variant.nomi.upper(), muqova_matni)
        self.assertIn("600000 – Aniq fanlar", muqova_matni)
        self.assertIn(str(self.yil), muqova_matni)
        self.assertIn(f"{self.kafedra.nomi} kafedrasi", muqova_matni)

    def test_tuzuvchi_va_taqrizchi_bosh_qoldiriladi(self) -> None:
        from docx import Document

        buffer = dastur_render(self.variant)
        hujjat = Document(buffer)
        paragraphs = hujjat.paragraphs
        muqova_matni = "\n".join(p.text for p in paragraphs)
        self.assertNotIn("Komilov", muqova_matni)
        self.assertNotIn("Xashimov", muqova_matni)

        for label in ("Tuzuvchi:", "Taqrizchilar:"):
            idx = next(i for i, p in enumerate(paragraphs) if p.text == label)
            self.assertEqual(paragraphs[idx + 1].text, "")


class DasturFormatlashTest(TestCase):
    """Uses the raw template (plans.dastur.service.SABLON_YOLI), not a
    rendered document — docxtpl's {%tr %} loops add/remove rows based on
    context, so row counts are only stable before rendering."""

    def setUp(self) -> None:
        from docx import Document

        from plans.dastur.service import SABLON_YOLI

        self.hujjat = Document(SABLON_YOLI)

    def test_sahifa_olchami_letter(self) -> None:
        bolim = self.hujjat.sections[0]
        self.assertEqual(bolim.page_width.twips, 12240)
        self.assertEqual(bolim.page_height.twips, 15840)

    def test_shrift_times_new_roman(self) -> None:
        normal = self.hujjat.styles["Normal"]
        self.assertEqual(normal.font.name, "Times New Roman")
        rfonts = normal.font.element.get_or_add_rPr().find(qn("w:rFonts"))
        self.assertEqual(rfonts.get(qn("w:eastAsia")), "Times New Roman")
        self.assertEqual(rfonts.get(qn("w:cs")), "Times New Roman")

    def test_sarlavha_qatori_kulrang_fon(self) -> None:
        header_row = self.hujjat.tables[1].rows[0]
        tc = header_row.cells[0]._tc
        shd = tc.find(qn("w:tcPr")).find(qn("w:shd"))
        self.assertEqual(shd.get(qn("w:fill")), "D9D9D9")

    def test_jadval_tuzilishi_saqlanadi(self) -> None:
        self.assertEqual(len(self.hujjat.tables), 3)
        self.assertEqual(len(self.hujjat.tables[1].rows), 58)
        self.assertEqual(len(self.hujjat.tables[2].rows), 17)
