"""Demand, allocation and workload calculations over the plans schema."""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db.models import Sum

from accounts.models import Department, OqituvchiProfil
from plans.managers import FanSemestrQuerySet
from plans.models import (
    KURS_ISHI_SOAT_TALABAGA,
    PER_GURUH_TURLAR,
    Fan,
    FanSemestr,
    FanTuri,
    FanVariant,
    Guruh,
    OquvReja,
    SoatTuri,
    Yuklama,
)


@dataclass(frozen=True)
class TalabSatri:
    """Demand vs allocation for one (fan-semester, hour type) line."""

    fan_semestr: FanSemestr
    tur: str
    talab_soat: int | None  # None until talabalar/guruhlar soni is entered
    taqsimlangan_soat: int

    @property
    def qoldiq_soat(self) -> int | None:
        if self.talab_soat is None:
            return None
        return self.talab_soat - self.taqsimlangan_soat


@dataclass(frozen=True)
class YuklamaHolati:
    """One teacher's annual standing against the position minimum."""

    oqituvchi: OqituvchiProfil
    jami_soat: int
    min_soat: int

    @property
    def kamomad(self) -> int:
        return max(0, self.min_soat - self.jami_soat)


def guruhlarni_sinxronlash(reja: OquvReja) -> list[Guruh]:
    """Grow/shrink named groups to match guruhlar_soni.

    Surplus groups carrying yuklamalar are kept — deleting them would orphan
    real delegation work; the admin sees them until assignments move.
    """
    soni = reja.guruhlar_soni or 0
    prefiks = reja.guruh_prefiksi or reja.yonalish_kodi
    for raqam in range(1, soni + 1):
        Guruh.objects.get_or_create(
            reja=reja,
            raqam=raqam,
            defaults={"nomi": f"{prefiks}-{reja.boshlanish_yili}-{raqam}"},
        )
    reja.guruhlar.filter(raqam__gt=soni, yuklamalar__isnull=True).delete()
    return list(reja.guruhlar.all())


def fan_semestr_talabi(fs: FanSemestr, reja: OquvReja) -> dict[str, int | None]:
    """Hour demand per type: lecture x1, per-group types x groups, kurs ishi
    2h x students. Types with no hours are omitted."""
    talab: dict[str, int | None] = {}
    if fs.maruza_soat:
        talab[SoatTuri.MARUZA] = fs.maruza_soat
    for tur in PER_GURUH_TURLAR:
        soat = fs.tur_soat(tur)
        if soat:
            talab[tur] = soat * reja.guruhlar_soni if reja.guruhlar_soni else None
    if fs.kurs_ishi_bor:
        talab[SoatTuri.KURS_ISHI] = (
            KURS_ISHI_SOAT_TALABAGA * reja.talabalar_soni
            if reja.talabalar_soni
            else None
        )
    return talab


def taqsimot_hisoboti(
    reja: OquvReja,
    *,
    kurs: int | None = None,
    kafedra: Department | None = None,
) -> list[TalabSatri]:
    semestrlar = FanSemestr.objects.reja_uchun(reja).effektiv()
    if kurs is not None:
        semestrlar = semestrlar.oquv_yilida(kurs)
    if kafedra is not None:
        semestrlar = semestrlar.filter(variant__kafedra=kafedra)
    return _talab_satrlari(semestrlar)


def kafedra_taqsimoti(kafedra: Department, akademik_yil: int) -> list[TalabSatri]:
    semestrlar = (
        FanSemestr.objects.effektiv()
        .akademik_yilda(akademik_yil)
        .filter(variant__kafedra=kafedra)
    )
    return _talab_satrlari(semestrlar)


def ofis_taqsimoti(akademik_yil: int) -> list[TalabSatri]:
    """Institution-wide demand vs allocation for one academic year."""
    return _talab_satrlari(FanSemestr.objects.effektiv().akademik_yilda(akademik_yil))


def _talab_satrlari(semestrlar: FanSemestrQuerySet) -> list[TalabSatri]:
    semestrlar = semestrlar.select_related("variant__fan__reja")
    taqsimlangan = taqsimlangan_soatlar(semestrlar)
    return [
        TalabSatri(
            fan_semestr=fs,
            tur=tur,
            talab_soat=talab,
            taqsimlangan_soat=taqsimlangan.get((fs.pk, tur), 0),
        )
        for fs in semestrlar
        for tur, talab in fan_semestr_talabi(fs, fs.variant.fan.reja).items()
    ]


def taqsimlangan_soatlar(
    semestrlar: FanSemestrQuerySet,
) -> dict[tuple[int, str], int]:
    """Allocated hours grouped by (fan_semestr, tur); reused by dashboards."""
    qatorlar = (
        Yuklama.objects.filter(fan_semestr__in=semestrlar)
        .values("fan_semestr_id", "tur")
        .annotate(jami=Sum("soat"))
    )
    return {(q["fan_semestr_id"], q["tur"]): q["jami"] for q in qatorlar}


def oqituvchi_yillik_yuklamasi(oqituvchi: OqituvchiProfil, akademik_yil: int) -> int:
    jami = (
        Yuklama.objects.filter(oqituvchi=oqituvchi)
        .akademik_yilda(akademik_yil)
        .aggregate(jami=Sum("soat"))["jami"]
    )
    return jami or 0


def yuklama_kamomadi(
    akademik_yil: int, *, kafedra: Department | None = None
) -> list[YuklamaHolati]:
    """Every teacher's annual hours vs min_soat; zero-hour teachers included."""
    oqituvchilar = OqituvchiProfil.objects.select_related("foydalanuvchi", "turi")
    if kafedra is not None:
        oqituvchilar = oqituvchilar.filter(kafedra=kafedra)
    soatlar = dict(
        Yuklama.objects.akademik_yilda(akademik_yil)
        .values_list("oqituvchi_id")
        .annotate(jami=Sum("soat"))
    )
    holatlar = [
        YuklamaHolati(
            oqituvchi=o, jami_soat=soatlar.get(o.pk, 0), min_soat=o.turi.min_soat
        )
        for o in oqituvchilar
    ]
    return sorted(holatlar, key=lambda h: h.kamomad, reverse=True)


def variantni_tanlash(fan: Fan, variant: FanVariant) -> None:
    """Office head picks the taught alternative of a selective slot."""
    if fan.turi != FanTuri.TANLOV:
        raise ValidationError("Faqat tanlov fanlari uchun variant tanlanadi.")
    if variant.fan_id != fan.pk:
        raise ValidationError("Variant boshqa fanga tegishli.")
    fan.tanlangan_variant = variant
    fan.save(update_fields=["tanlangan_variant"])


def kafedraga_biriktirish(variant: FanVariant, kafedra: Department | None) -> None:
    """Office head delegates (or re-delegates) a course to a department."""
    if variant.fan.tanlangan_variant_id != variant.pk:
        raise ValidationError("Avval fan variantini tanlang.")
    if variant.kafedra_id is not None and kafedra != variant.kafedra:
        # Moving or clearing the kafedra would orphan its teachers' delegations.
        if Yuklama.objects.filter(fan_semestr__variant=variant).exists():
            raise ValidationError("Fanda yuklamalar bor — avval ularni bekor qiling.")
    variant.kafedra = kafedra
    variant.save(update_fields=["kafedra"])
