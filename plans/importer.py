"""Persist a parsed o'quv reja into the plans schema."""

import re
from dataclasses import dataclass
from pathlib import Path

import openpyxl
from django.db import transaction
from django.utils import timezone

from parser.models import Alternative, Course, SelectiveSlot
from parser.parser import (
    detect_sheet_layout,
    extract_start_year,
    find_cell_containing,
    parse_core_courses,
    parse_selective_courses,
    read_metadata,
    resolve_direction,
)
from plans.models import Fan, FanSemestr, FanTuri, FanVariant, OquvReja, Yuklama
from plans.split import split_breakdown


class ImportXato(Exception):
    """A file cannot be imported; the message is user-facing."""


@dataclass(frozen=True)
class ParsedReja:
    yonalish_kodi: str
    yonalish_nomi: str
    boshlanish_yili: int
    daraja: str
    davomiylik_yil: int
    talim_shakli: str
    fayl_nomi: str
    core: list[Course]
    slots: list[SelectiveSlot]


@dataclass
class ImportNatija:
    reja: OquvReja
    fan_soni: int
    variant_soni: int
    yaratildi: bool
    ogohlantirishlar: list[str]


def parse_xlsx(path: Path, boshlanish_yili: int | None = None) -> ParsedReja:
    ws = openpyxl.load_workbook(path, data_only=True).active
    direction = resolve_direction(ws)
    if direction is None or not direction[0]:
        raise ImportXato("yo'nalish kodi topilmadi — reja identifikatsiya qilinmaydi")
    if boshlanish_yili is None:
        boshlanish_yili = _varaqdagi_boshlanish_yili(ws)
    daraja, davomiylik_matni, talim_shakli = read_metadata(ws)
    layout, semester_map, weekly_map = detect_sheet_layout(ws)
    return ParsedReja(
        yonalish_kodi=direction[0],
        yonalish_nomi=_bir_qatorga(direction[1], 255),
        boshlanish_yili=boshlanish_yili,
        daraja=_bir_qatorga(daraja, 100),
        davomiylik_yil=_davomiylik_yillari(davomiylik_matni),
        talim_shakli=_bir_qatorga(talim_shakli, 100),
        fayl_nomi=path.name,
        core=parse_core_courses(ws, layout, semester_map, weekly_map),
        slots=parse_selective_courses(ws, layout, semester_map, weekly_map),
    )


def _varaqdagi_boshlanish_yili(ws: object) -> int:
    yil_katak = find_cell_containing(ws, "quv yili")
    boshlanish = extract_start_year(str(yil_katak.value)) if yil_katak else ""
    if not boshlanish:
        raise ImportXato(
            "o'quv yili topilmadi — boshlanish yilini --yil bilan ko'rsating"
        )
    return int(boshlanish)


def _davomiylik_yillari(matn: str) -> int:
    match = re.search(r"(\d+)\s*yil", matn)
    return int(match.group(1)) if match else 4


def _bir_qatorga(matn: str, uzunlik: int) -> str:
    # Some sheets merge several metadata labels into one multi-line cell;
    # store a single-line, field-length-safe version.
    return " ".join(matn.split())[:uzunlik]


@transaction.atomic
def import_reja(parsed: ParsedReja, *, replace: bool = False) -> ImportNatija:
    reja, yaratildi, holat = _rejani_tayyorlash(parsed, replace)
    ogohlantirishlar: list[str] = []
    for course in parsed.core:
        ogohlantirishlar += _majburiy_fan_yaratish(reja, course)
    for slot in parsed.slots:
        ogohlantirishlar += _tanlov_fan_yaratish(reja, slot)
    if holat is not None:
        ogohlantirishlar += _manual_holatni_tiklash(reja, holat)
    return ImportNatija(
        reja=reja,
        fan_soni=reja.fanlar.count(),
        variant_soni=FanVariant.objects.filter(fan__reja=reja).count(),
        yaratildi=yaratildi,
        ogohlantirishlar=ogohlantirishlar,
    )


def _rejani_tayyorlash(
    parsed: ParsedReja, replace: bool
) -> tuple[OquvReja, bool, dict | None]:
    """Create the reja or, on re-import, empty it while keeping manual state."""
    yangilanadigan = {
        "yonalish_nomi": parsed.yonalish_nomi,
        "daraja": parsed.daraja,
        "davomiylik_yil": parsed.davomiylik_yil,
        "manba_fayl": parsed.fayl_nomi,
        "import_vaqti": timezone.now(),
    }
    reja, yaratildi = OquvReja.objects.get_or_create(
        yonalish_kodi=parsed.yonalish_kodi,
        boshlanish_yili=parsed.boshlanish_yili,
        talim_shakli=parsed.talim_shakli,
        defaults=yangilanadigan,
    )
    if yaratildi:
        return reja, True, None
    if not replace:
        raise ImportXato(
            f"{reja} allaqachon import qilingan; --replace bilan qayta yuklang"
        )
    yuklamalar = Yuklama.objects.filter(fan_semestr__variant__fan__reja=reja).count()
    if yuklamalar:
        raise ImportXato(
            f"{reja} bo'yicha {yuklamalar} ta yuklama taqsimlangan; "
            "avval yuklamalarni o'chiring"
        )
    holat = _manual_holatni_saqlash(reja)
    reja.fanlar.all().delete()
    for maydon, qiymat in yangilanadigan.items():
        setattr(reja, maydon, qiymat)
    reja.save()
    return reja, False, holat


def _majburiy_fan_yaratish(reja: OquvReja, course: Course) -> list[str]:
    fan = Fan.objects.create(
        reja=reja, raqam=course.num, turi=FanTuri.MAJBURIY, jami_soat=course.hours
    )
    variant = _variant_yaratish(fan, course.code, course.name, course)
    ogohlantirishlar = _variant_semestrlari(
        variant, course.semester_credits, course.semester_weekly_hours
    )
    fan.tanlangan_variant = variant
    fan.save(update_fields=["tanlangan_variant"])
    return [f"{fan.raqam} {course.name}: {o}" for o in ogohlantirishlar]


def _tanlov_fan_yaratish(reja: OquvReja, slot: SelectiveSlot) -> list[str]:
    fan = Fan.objects.create(
        reja=reja, raqam=slot.num, turi=FanTuri.TANLOV, jami_soat=slot.hours
    )
    ogohlantirishlar: list[str] = []
    if not slot.alternatives:
        return [f"{fan.raqam}: tanlov slotida variantlar topilmadi"]
    for alt in slot.alternatives:
        if fan.variantlar.filter(kodi=alt.code, nomi=alt.name).exists():
            ogohlantirishlar.append(
                f"{fan.raqam} {alt.name}: takroriy variant tashlab yuborildi"
            )
            continue
        variant = _variant_yaratish(fan, alt.code, alt.name, alt)
        # Alternatives share the slot's semester distribution by format design.
        semestr_ogohlantirishlari = _variant_semestrlari(
            variant, slot.semester_credits, slot.semester_weekly_hours
        )
        ogohlantirishlar += [
            f"{fan.raqam} {alt.name}: {o}" for o in semestr_ogohlantirishlari
        ]
    return ogohlantirishlar


def _variant_yaratish(
    fan: Fan, kodi: str, nomi: str, soatlar: Course | Alternative
) -> FanVariant:
    return FanVariant.objects.create(
        fan=fan,
        kodi=kodi or "",
        nomi=nomi,
        auditoriya_soat=soatlar.classroom,
        maruza_soat=soatlar.lecture,
        amaliyot_soat=soatlar.practice,
        laboratoriya_soat=soatlar.lab,
        seminar_soat=soatlar.seminar,
        kurs_ishi_soat=soatlar.course_proj,
    )


def _variant_semestrlari(
    variant: FanVariant, credits: dict[int, int], weekly: dict[int, int]
) -> list[str]:
    satrlar, ogohlantirishlar = split_breakdown(
        variant.maruza_soat,
        variant.amaliyot_soat,
        variant.laboratoriya_soat,
        variant.seminar_soat,
        weekly,
        credits,
    )
    semestrlar = [
        FanSemestr(
            variant=variant,
            semestr=semestr,
            kredit=credits.get(semestr, 0),
            haftalik_soat=weekly.get(semestr, 0),
            **maydonlar,
        )
        for semestr, maydonlar in sorted(satrlar.items())
    ]
    if variant.kurs_ishi_soat > 0 and semestrlar:
        # Owner's rule: the course project lands in the course's final semester.
        semestrlar[-1].kurs_ishi_bor = True
    FanSemestr.objects.bulk_create(semestrlar)
    return ogohlantirishlar


def _manual_holatni_saqlash(reja: OquvReja) -> dict:
    """Snapshot kafedra links and tanlov selections keyed by stable identity."""
    kafedralar = {
        (v.fan.raqam, v.kodi, v.nomi): v.kafedra_id
        for v in FanVariant.objects.filter(
            fan__reja=reja, kafedra__isnull=False
        ).select_related("fan")
    }
    tanlovlar = {
        fan.raqam: (fan.tanlangan_variant.kodi, fan.tanlangan_variant.nomi)
        for fan in reja.fanlar.filter(
            turi=FanTuri.TANLOV, tanlangan_variant__isnull=False
        ).select_related("tanlangan_variant")
    }
    return {"kafedralar": kafedralar, "tanlovlar": tanlovlar}


def _manual_holatni_tiklash(reja: OquvReja, holat: dict) -> list[str]:
    ogohlantirishlar = []
    for (raqam, kodi, nomi), kafedra_id in holat["kafedralar"].items():
        soni = FanVariant.objects.filter(
            fan__reja=reja, fan__raqam=raqam, kodi=kodi, nomi=nomi
        ).update(kafedra_id=kafedra_id)
        if not soni:
            ogohlantirishlar.append(
                f"{raqam} {nomi}: kafedra biriktirmasi tiklanmadi (fan o'zgargan)"
            )
    for raqam, (kodi, nomi) in holat["tanlovlar"].items():
        variant = FanVariant.objects.filter(
            fan__reja=reja, fan__raqam=raqam, kodi=kodi, nomi=nomi
        ).first()
        if variant is None:
            ogohlantirishlar.append(
                f"{raqam} {nomi}: tanlov qarori tiklanmadi (variant o'zgargan)"
            )
        else:
            Fan.objects.filter(reja=reja, raqam=raqam).update(tanlangan_variant=variant)
    return ogohlantirishlar
