from io import BytesIO
from pathlib import Path

import openpyxl
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from plans.importer import ImportXato, parse_xlsx
from plans.models import OquvReja
from plans.tests.factories import make_yonalish
from plans.uploads import YuklashParametrlari, fayldan_import_qilish

BHA = (
    Path(__file__).resolve().parents[2]
    / "sources"
    / "(24-25) Buxgalteriya hisobi eng, it 21.08.2024.xlsx"
)


def _parametrlar(**kwargs: object) -> YuklashParametrlari:
    maydonlar: dict[str, object] = {
        "talabalar_soni": 50,
        "guruhlar_soni": 2,
        "guruh_prefiksi": "BH",
        "boshlanish_yili": 2025,
        "replace": False,
    }
    maydonlar.update(kwargs)
    return YuklashParametrlari(**maydonlar)


class FayldanImportTests(TestCase):
    def test_haqiqiy_fayl_import_qilinadi(self) -> None:
        yonalish_kodi = parse_xlsx(BHA, boshlanish_yili=2025).yonalish_kodi
        make_yonalish(kodi=yonalish_kodi)
        fayl = SimpleUploadedFile("BHA.xlsx", BHA.read_bytes())

        natija = fayldan_import_qilish(fayl, _parametrlar())

        reja = OquvReja.objects.get(pk=natija.reja.pk)
        self.assertTrue(natija.yaratildi)
        self.assertGreater(natija.fan_soni, 0)
        self.assertEqual(reja.talabalar_soni, 50)
        self.assertEqual(reja.guruhlar_soni, 2)
        guruh_nomlari = list(reja.guruhlar.values_list("nomi", flat=True))
        self.assertEqual(guruh_nomlari, ["BH-2025-1", "BH-2025-2"])

    def test_notogri_fayl_import_xato(self) -> None:
        fayl = SimpleUploadedFile("reja.xlsx", b"bu excel emas")
        with self.assertRaises(ImportXato):
            fayldan_import_qilish(fayl, _parametrlar())

    def test_bosh_varaq_import_xato(self) -> None:
        kitob = openpyxl.Workbook()
        xotira = BytesIO()
        kitob.save(xotira)
        fayl = SimpleUploadedFile("bosh.xlsx", xotira.getvalue())
        with self.assertRaises(ImportXato):
            fayldan_import_qilish(fayl, _parametrlar())
