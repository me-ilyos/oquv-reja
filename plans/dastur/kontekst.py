"""Builds the docxtpl render context for one FanVariant's o'quv dastur."""

from django.utils import timezone

from accounts.models import Universitet
from plans.dastur.mavzular import bosh_mavzular
from plans.models import FanSemestr, FanVariant

BLANK = "_____"


def dastur_kontekst(variant: FanVariant) -> dict[str, object]:
    fan = variant.fan
    reja = fan.reja
    semestrlar = list(variant.semestrlar.order_by("semestr"))
    mustaqil_soat = max((fan.jami_soat or 0) - variant.auditoriya_soat, 0)

    return {
        "university": _universitet_nomi(),
        "kafedra": variant.kafedra.nomi if variant.kafedra else "",
        "kafedra_council": {"year": BLANK, "date": BLANK},
        "major": {
            "bilim_sohasi": _soha(reja.bilim_sohasi_kodi, reja.bilim_sohasi_nomi),
            "talim_sohasi": _soha(reja.talim_sohasi_kodi, reja.talim_sohasi_nomi),
            "talim_yonalishi": _soha(reja.yonalish_kodi, reja.yonalish_nomi),
        },
        "education_form": reja.talim_shakli.lower(),
        "year": _muqova_yili(semestrlar),
        "course": {
            "code": variant.kodi,
            "name": variant.nomi,
            "module_type": fan.get_turi_display(),
        },
        "academic_years_str": _oquv_yillari_matni(semestrlar),
        "semesters_str": ", ".join(str(fs.semestr) for fs in semestrlar),
        "credits_str": ", ".join(str(fs.kredit) for fs in semestrlar),
        "weekly_hours_str": ", ".join(str(fs.haftalik_soat) for fs in semestrlar),
        "plan_number": f"{reja.yonalish_kodi}-{fan.raqam}",
        "total_hours": _soat_matni(fan.jami_soat or 0),
        "classroom_total": _soat_matni(variant.auditoriya_soat),
        "hours": {
            "lecture": _soat_matni(variant.maruza_soat),
            "practice": _soat_matni(variant.amaliyot_soat),
            "lab": _soat_matni(variant.laboratoriya_soat),
            "seminar": _soat_matni(variant.seminar_soat),
            "self_study": _soat_matni(mustaqil_soat),
            "coursework": _soat_matni(variant.kurs_ishi_soat),
        },
        "lectures": bosh_mavzular(variant.maruza_soat, "M"),
        "practicals": bosh_mavzular(variant.amaliyot_soat, "A"),
        "labs": bosh_mavzular(variant.laboratoriya_soat, "L"),
        "seminars": bosh_mavzular(variant.seminar_soat, "S"),
    }


def _soha(kodi: str, nomi: str) -> str:
    return f"{kodi} – {nomi}" if kodi else nomi


def _soat_matni(soat: int) -> str:
    return str(soat) if soat else "-"


def _oquv_yillari_matni(semestrlar: list[FanSemestr]) -> str:
    yillar = sorted({fs.akademik_yil for fs in semestrlar})
    return ", ".join(f"{yil}/{yil + 1}" for yil in yillar)


def _muqova_yili(semestrlar: list[FanSemestr]) -> int:
    if not semestrlar:
        return timezone.now().year
    return min(fs.akademik_yil for fs in semestrlar)


def _universitet_nomi() -> str:
    universitet = Universitet.objects.first()
    return universitet.rasmiy_nomi if universitet else "Turan International University"
