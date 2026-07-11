"""Read-only aggregation feeding the office and kafedra dashboards.

Past academic years are never offered: the UI's year selector is built only
from tanlanadigan_yillar(), which floors at the current academic year.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from django.db.models import Count, Sum
from django.utils import timezone

from accounts.models import Department
from plans.models import Fan, FanSemestr, FanVariant, OquvReja
from plans.services import (
    TalabSatri,
    fan_semestr_talabi,
    ofis_taqsimoti,
    taqsimlangan_soatlar,
)


def joriy_akademik_yil(bugun: date | None = None) -> int:
    """O'quv yili sentyabrda boshlanadi: 2026-07 -> 2025 ("2025/2026")."""
    bugun = bugun or timezone.localdate()
    return bugun.year if bugun.month >= 9 else bugun.year - 1


def tanlanadigan_yillar() -> list[int]:
    """Academic years offered in the UI: current and future only.

    Built over ALL FanSemestr rows (not just effektiv) so a year containing
    only unselected tanlov slots still appears.
    """
    joriy = joriy_akademik_yil()
    yillar = (
        FanSemestr.objects.akademik_yil_bilan()
        # Model ordering leaks semestr into SELECT DISTINCT; clear it.
        .order_by()
        .values_list("akademik_yili", flat=True)
        .distinct()
    )
    return sorted(y for y in yillar if y >= joriy)


@dataclass(frozen=True)
class DashboardStat:
    """KPI card values computed from one list of TalabSatri rows."""

    jami_soat: int
    tur_soatlari: dict[str, int]
    kafedraga_biriktirilgan_soat: int
    kafedraga_biriktirilmagan_soat: int
    oqituvchiga_taqsimlangan_soat: int
    taqsimlanmagan_soat: int
    nomalum_talab_soni: int


def statlarni_hisoblash(satrlar: list[TalabSatri]) -> DashboardStat:
    tur_soatlari: dict[str, int] = defaultdict(int)
    biriktirilgan = biriktirilmagan = taqsimlangan = taqsimlanmagan = nomalum = 0
    for satr in satrlar:
        taqsimlangan += satr.taqsimlangan_soat
        if satr.talab_soat is None:
            nomalum += 1
            continue
        tur_soatlari[satr.tur] += satr.talab_soat
        if satr.fan_semestr.variant.kafedra_id is None:
            biriktirilmagan += satr.talab_soat
        else:
            biriktirilgan += satr.talab_soat
        taqsimlanmagan += max(0, satr.qoldiq_soat)
    return DashboardStat(
        jami_soat=sum(tur_soatlari.values()),
        tur_soatlari=dict(tur_soatlari),
        kafedraga_biriktirilgan_soat=biriktirilgan,
        kafedraga_biriktirilmagan_soat=biriktirilmagan,
        oqituvchiga_taqsimlangan_soat=taqsimlangan,
        taqsimlanmagan_soat=taqsimlanmagan,
        nomalum_talab_soni=nomalum,
    )


def jami_talabalar(akademik_yil: int) -> int:
    reja_idlar = (
        FanSemestr.objects.akademik_yilda(akademik_yil)
        .values_list("variant__fan__reja_id", flat=True)
        .distinct()
    )
    jami = OquvReja.objects.filter(pk__in=reja_idlar).aggregate(
        jami=Sum("talabalar_soni")
    )["jami"]
    return jami or 0


@dataclass(frozen=True)
class FanSatri:
    """One dashboard course row: a fan's in-year demand and allocation."""

    fan: Fan
    fan_semestrlar: list[FanSemestr]
    tur_soatlari: dict[str, int | None]
    taqsimlangan_soat: int
    kafedra: Department | None
    tanlanmagan: bool

    @property
    def jami_soat(self) -> int:
        return sum(soat for soat in self.tur_soatlari.values() if soat)

    @property
    def biriktirilmagan(self) -> bool:
        return self.kafedra is None

    @property
    def variant(self) -> "FanVariant":
        """Selected variant, or the representative one for unselected tanlov."""
        return self.fan.tanlangan_variant or self.fan_semestrlar[0].variant


def ofis_fan_satrlari(akademik_yil: int) -> list[FanSatri]:
    """Course rows for the office dashboard, unallocated ones flagged.

    Unselected tanlov slots are included with their first variant's semesters
    as representative demand — alternatives share the slot's semester
    distribution by importer design.
    """
    satrlar = _effektiv_satrlar(akademik_yil) + _tanlov_satrlari(akademik_yil)
    return sorted(satrlar, key=lambda satr: (satr.fan.reja_id, satr.fan.raqam))


def _effektiv_satrlar(akademik_yil: int) -> list[FanSatri]:
    semestrlar = (
        FanSemestr.objects.effektiv()
        .akademik_yilda(akademik_yil)
        .select_related("variant__fan__reja", "variant__kafedra")
        .order_by("semestr")
    )
    taqsimlangan = taqsimlangan_soatlar(semestrlar)
    guruhlar: dict[int, list[FanSemestr]] = defaultdict(list)
    for fs in semestrlar:
        guruhlar[fs.variant.fan_id].append(fs)
    return [
        FanSatri(
            fan=fslar[0].variant.fan,
            fan_semestrlar=fslar,
            tur_soatlari=_tur_yigindisi(fslar),
            taqsimlangan_soat=sum(
                soat
                for (fs_pk, _), soat in taqsimlangan.items()
                if fs_pk in {fs.pk for fs in fslar}
            ),
            kafedra=fslar[0].variant.kafedra,
            tanlanmagan=False,
        )
        for fslar in guruhlar.values()
    ]


def _tanlov_satrlari(akademik_yil: int) -> list[FanSatri]:
    yildagi = FanSemestr.objects.akademik_yilda(akademik_yil)
    fanlar = (
        Fan.objects.tanlov_kutilmoqda()
        .filter(variantlar__semestrlar__in=yildagi)
        .distinct()
        .select_related("reja")
    )
    satrlar = []
    for fan in fanlar:
        fslar = list(yildagi.filter(variant__fan=fan).order_by("variant_id", "semestr"))
        birinchi_variant = fslar[0].variant_id
        fslar = [fs for fs in fslar if fs.variant_id == birinchi_variant]
        satrlar.append(
            FanSatri(
                fan=fan,
                fan_semestrlar=fslar,
                tur_soatlari=_tur_yigindisi(fslar),
                taqsimlangan_soat=0,
                kafedra=None,
                tanlanmagan=True,
            )
        )
    return satrlar


def _tur_yigindisi(fslar: list[FanSemestr]) -> dict[str, int | None]:
    """Sum per-type demand over semesters; None (count missing) is sticky."""
    jami: dict[str, int | None] = {}
    for fs in fslar:
        for tur, soat in fan_semestr_talabi(fs, fs.variant.fan.reja).items():
            if tur not in jami:
                jami[tur] = soat
            elif jami[tur] is None or soat is None:
                jami[tur] = None
            else:
                jami[tur] += soat
    return jami


@dataclass(frozen=True)
class SemestrovkaSatri:
    """One reja-detail row: a fan's weekly load across every semester."""

    fan: Fan
    variant: FanVariant
    semestr_soatlari: dict[int, FanSemestr]
    tanlanmagan: bool

    @property
    def kafedra(self) -> Department | None:
        return self.variant.kafedra if not self.tanlanmagan else None

    @property
    def biriktirilmagan(self) -> bool:
        return self.kafedra is None


def reja_semestrovkasi(reja: OquvReja) -> list[SemestrovkaSatri]:
    """The semestrovka: per-fan per-semester split rows for one reja."""
    fanlar = reja.fanlar.select_related("tanlangan_variant__kafedra").prefetch_related(
        "variantlar__semestrlar"
    )
    satrlar = []
    for fan in fanlar:
        variantlar = list(fan.variantlar.all())
        variant = fan.tanlangan_variant or (variantlar[0] if variantlar else None)
        if variant is None:
            continue
        satrlar.append(
            SemestrovkaSatri(
                fan=fan,
                variant=variant,
                semestr_soatlari={fs.semestr: fs for fs in variant.semestrlar.all()},
                tanlanmagan=fan.tanlangan_variant_id is None,
            )
        )
    return satrlar


@dataclass(frozen=True)
class KafedraQamrov:
    """Per-department coverage: delegated demand vs teacher-assigned hours."""

    kafedra: Department
    biriktirilgan_soat: int
    taqsimlangan_soat: int
    oqituvchilar_soni: int


def kafedra_qamrovi(akademik_yil: int) -> list[KafedraQamrov]:
    biriktirilgan: dict[int, int] = defaultdict(int)
    taqsimlangan: dict[int, int] = defaultdict(int)
    for satr in ofis_taqsimoti(akademik_yil):
        kafedra_id = satr.fan_semestr.variant.kafedra_id
        if kafedra_id is None:
            continue
        if satr.talab_soat:
            biriktirilgan[kafedra_id] += satr.talab_soat
        taqsimlangan[kafedra_id] += satr.taqsimlangan_soat
    kafedralar = Department.objects.annotate(
        oqituvchilar_soni=Count("oqituvchilar")
    ).order_by("nomi")
    return [
        KafedraQamrov(
            kafedra=kafedra,
            biriktirilgan_soat=biriktirilgan.get(kafedra.pk, 0),
            taqsimlangan_soat=taqsimlangan.get(kafedra.pk, 0),
            oqituvchilar_soni=kafedra.oqituvchilar_soni,
        )
        for kafedra in kafedralar
    ]
