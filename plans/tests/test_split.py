from django.test import SimpleTestCase

from plans.split import largest_remainder_split, semester_weights, split_breakdown


class LargestRemainderSplitTest(SimpleTestCase):
    def test_yigindisi_aniq_totalga_teng(self) -> None:
        natija = largest_remainder_split(100, {1: 1, 2: 1, 3: 1})
        self.assertEqual(sum(natija.values()), 100)
        self.assertEqual(natija, {1: 34, 2: 33, 3: 33})

    def test_proportsional_boladi(self) -> None:
        self.assertEqual(largest_remainder_split(60, {3: 4, 4: 4}), {3: 30, 4: 30})
        self.assertEqual(largest_remainder_split(90, {1: 2, 2: 4}), {1: 30, 2: 60})

    def test_teng_qoldiqda_kichik_semestr_yutadi(self) -> None:
        self.assertEqual(largest_remainder_split(5, {1: 1, 2: 1}), {1: 3, 2: 2})

    def test_bitta_semestr_toliq_oladi(self) -> None:
        self.assertEqual(largest_remainder_split(24, {2: 5}), {2: 24})

    def test_bosh_vaznlar_bosh_natija(self) -> None:
        self.assertEqual(largest_remainder_split(24, {}), {})

    def test_nol_total_nol_taqsimot(self) -> None:
        self.assertEqual(largest_remainder_split(0, {1: 2, 2: 3}), {1: 0, 2: 0})


class SemesterWeightsTest(SimpleTestCase):
    def test_haftalik_soat_ustun(self) -> None:
        self.assertEqual(semester_weights({1: 4}, {1: 2}), {1: 4})

    def test_kreditga_qaytadi(self) -> None:
        self.assertEqual(semester_weights({}, {1: 2, 2: 4}), {1: 2, 2: 4})

    def test_ikkalasi_bosh(self) -> None:
        self.assertEqual(semester_weights({}, {}), {})

    def test_faqat_kreditdagi_semestr_qoshiladi(self) -> None:
        # A semester present only in credits (weekly omits it) still gets a
        # weight — it must not silently lose its FanSemestr row.
        self.assertEqual(semester_weights({1: 4}, {1: 2, 2: 4}), {1: 4, 2: 4})


class SplitBreakdownTest(SimpleTestCase):
    def test_bir_semestrli_fan_ozgarishsiz(self) -> None:
        satrlar, ogohlantirishlar = split_breakdown(
            24, 24, 24, 0, weekly={1: 5}, credits={1: 4}
        )
        self.assertEqual(
            satrlar,
            {
                1: {
                    "maruza_soat": 24,
                    "amaliyot_soat": 24,
                    "laboratoriya_soat": 24,
                    "seminar_soat": 0,
                }
            },
        )
        # 5 * 15 = 75 != 72: real sheets round weekly hours, warn but keep data.
        self.assertEqual(len(ogohlantirishlar), 1)

    def test_kop_semestrli_fan_teng_bolinadi(self) -> None:
        satrlar, ogohlantirishlar = split_breakdown(
            60, 60, 0, 0, weekly={3: 4, 4: 4}, credits={}
        )
        self.assertEqual(satrlar[3]["maruza_soat"], 30)
        self.assertEqual(satrlar[4]["maruza_soat"], 30)
        self.assertEqual(satrlar[3]["amaliyot_soat"], 30)
        self.assertEqual(ogohlantirishlar, [])

    def test_komponent_yigindisi_saqlanadi(self) -> None:
        satrlar, _ = split_breakdown(
            45, 31, 7, 3, weekly={1: 3, 2: 2, 3: 1}, credits={}
        )
        for maydon, jami in [
            ("maruza_soat", 45),
            ("amaliyot_soat", 31),
            ("laboratoriya_soat", 7),
            ("seminar_soat", 3),
        ]:
            self.assertEqual(sum(satr[maydon] for satr in satrlar.values()), jami)

    def test_kredit_vaznlariga_qaytadi(self) -> None:
        satrlar, ogohlantirishlar = split_breakdown(
            30, 30, 0, 0, weekly={}, credits={1: 1, 2: 1}
        )
        self.assertEqual(satrlar[1]["maruza_soat"], 15)
        self.assertEqual(satrlar[2]["maruza_soat"], 15)
        # No weekly data: the 15-week cross-check cannot run.
        self.assertEqual(ogohlantirishlar, [])

    def test_taqsimot_umuman_yoq(self) -> None:
        satrlar, ogohlantirishlar = split_breakdown(30, 30, 0, 0, weekly={}, credits={})
        self.assertEqual(satrlar, {})
        self.assertEqual(len(ogohlantirishlar), 1)

    def test_mos_kelmaslik_ogohlantiradi(self) -> None:
        _, ogohlantirishlar = split_breakdown(30, 30, 0, 0, weekly={1: 2}, credits={})
        self.assertTrue(any("teng emas" in o for o in ogohlantirishlar))
