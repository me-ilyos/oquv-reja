"""Orchestrate a browser-uploaded reja file into the importer."""

import uuid
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from plans.importer import ImportNatija, ImportXato, import_reja, parse_xlsx
from plans.services import guruhlarni_sinxronlash

YUKLASH_KATALOGI = "rejalar"


@dataclass(frozen=True)
class YuklashParametrlari:
    bilim_sohasi_kodi: str
    bilim_sohasi_nomi: str
    talim_sohasi_kodi: str
    talim_sohasi_nomi: str
    talabalar_soni: int
    guruhlar_soni: int
    guruh_prefiksi: str
    boshlanish_yili: int | None
    replace: bool


def fayldan_import_qilish(
    fayl: UploadedFile, parametrlar: YuklashParametrlari
) -> ImportNatija:
    """Save the upload, parse it and persist reja + counts atomically.

    ImportXato propagates with its user-facing Uzbek message; the saved file
    is kept either way so a failed sheet can be inspected.
    """
    yol = _faylni_saqlash(fayl)
    try:
        parsed = parse_xlsx(yol, parametrlar.boshlanish_yili)
    except BadZipFile as xato:
        raise ImportXato("fayl .xlsx formatida emas yoki buzilgan") from xato
    with transaction.atomic():
        natija = import_reja(
            parsed,
            bilim_sohasi_kodi=parametrlar.bilim_sohasi_kodi,
            bilim_sohasi_nomi=parametrlar.bilim_sohasi_nomi,
            talim_sohasi_kodi=parametrlar.talim_sohasi_kodi,
            talim_sohasi_nomi=parametrlar.talim_sohasi_nomi,
            replace=parametrlar.replace,
        )
        reja = natija.reja
        reja.talabalar_soni = parametrlar.talabalar_soni
        reja.guruhlar_soni = parametrlar.guruhlar_soni
        reja.guruh_prefiksi = parametrlar.guruh_prefiksi
        reja.save(update_fields=["talabalar_soni", "guruhlar_soni", "guruh_prefiksi"])
        guruhlarni_sinxronlash(reja)
    return natija


def _faylni_saqlash(fayl: UploadedFile) -> Path:
    katalog = Path(settings.MEDIA_ROOT) / YUKLASH_KATALOGI
    katalog.mkdir(parents=True, exist_ok=True)
    yol = katalog / f"{uuid.uuid4().hex[:8]}_{Path(fayl.name).name}"
    with open(yol, "wb") as nishon:
        for parcha in fayl.chunks():
            nishon.write(parcha)
    return yol
