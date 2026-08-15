"""Renders the official o'quv dastur (.docx) for one course, pre-filled from
data already in the DB. Content the system has no source for (purpose,
outcomes, literature, per-topic breakdowns, ...) is left blank for the
teacher to fill in afterward in Word.
"""

from io import BytesIO
from pathlib import Path

from django.utils import timezone
from docxtpl import DocxTemplate

from accounts.models import OqituvchiProfil, Universitet
from plans.models import FanVariant, SoatTuri, Yuklama

SABLON_YOLI = Path(__file__).resolve().parent / "oquv_dastur.docx"

# Council/protocol references are filled in by hand after generation.
BLANK = "_____"


def dastur_egasimi(variant: FanVariant, oqituvchi: OqituvchiProfil) -> bool:
    """True if `oqituvchi` holds this course's lecture (MARUZA).

    A FanVariant's semesters already belong to one fixed curriculum year via
    its OquvReja, so there is nothing to compare against "today" — filtering
    by the calendar's current academic year would wrongly reject the real
    owner whenever that year has no imported data yet.
    """
    return Yuklama.objects.filter(
        fan_semestr__variant=variant, tur=SoatTuri.MARUZA, oqituvchi=oqituvchi
    ).exists()


def dastur_kontekst(variant: FanVariant) -> dict[str, object]:
    fan = variant.fan
    reja = fan.reja
    semestrlar = list(variant.semestrlar.order_by("semestr"))

    return {
        "university": _universitet_nomi(),
        "faculty": variant.kafedra.fakultet if variant.kafedra else "",
        "kafedra": variant.kafedra.nomi if variant.kafedra else "",
        "major": {
            "bilim_sohasi": reja.bilim_sohasi_nomi,
            "talim_sohasi": reja.talim_sohasi_nomi,
            "talim_yonalishi": reja.yonalish_nomi,
        },
        "education_form": reja.talim_shakli,
        "city": "",
        "year": timezone.now().year,
        "faculty_council": {"year": BLANK, "date": BLANK, "number": BLANK},
        "kafedra_council": {"year": BLANK, "date": BLANK, "number": BLANK},
        "authors": _mualliflar(variant),
        "reviewers": [],
        "course": {
            "code": variant.kodi,
            "name": variant.nomi,
            "module_type": fan.get_turi_display(),
        },
        "academic_years_str": ", ".join(str(fs.akademik_yil) for fs in semestrlar),
        "semesters_str": ", ".join(str(fs.semestr) for fs in semestrlar),
        "credits_str": ", ".join(str(fs.kredit) for fs in semestrlar),
        "weekly_hours_str": ", ".join(str(fs.haftalik_soat) for fs in semestrlar),
        "language": "",
        "plan_number": fan.raqam,
        "total_hours": fan.jami_soat,
        "classroom_total": variant.auditoriya_soat,
        "hours": {
            "lecture": variant.maruza_soat,
            "practice": variant.amaliyot_soat,
            "lab": variant.laboratoriya_soat,
            "self_study": "",
            "coursework": variant.kurs_ishi_soat,
        },
        "purpose": "",
        "tasks": "",
        "prerequisites": [],
        "outcomes": {"professional": [], "skills": []},
        "lectures": [],
        "practicals": [],
        "labs": [],
        "self_study_tasks": [],
        "methods": [],
        "credit_requirements": "",
        "literature": {"main": [], "additional": [], "online": []},
    }


def _universitet_nomi() -> str:
    universitet = Universitet.objects.first()
    return universitet.rasmiy_nomi if universitet else ""


def _mualliflar(variant: FanVariant) -> list[str]:
    """All teachers delegated on this course, lecture owner first."""
    yuklamalar = Yuklama.objects.filter(fan_semestr__variant=variant).select_related(
        "oqituvchi__foydalanuvchi", "oqituvchi__turi"
    )
    tartib = {t: i for i, t in enumerate(SoatTuri.values)}
    profillar: dict[int, OqituvchiProfil] = {}
    birinchi_tur: dict[int, str] = {}
    for yuklama in yuklamalar:
        profil = yuklama.oqituvchi
        if (
            profil.pk not in profillar
            or tartib[yuklama.tur] < tartib[birinchi_tur[profil.pk]]
        ):
            profillar[profil.pk] = profil
            birinchi_tur[profil.pk] = yuklama.tur
    tartiblangan = sorted(
        profillar.values(),
        key=lambda p: (tartib[birinchi_tur[p.pk]], str(p.foydalanuvchi)),
    )
    return [f"{p.foydalanuvchi}, {p.turi.nomi}" for p in tartiblangan]


def dastur_render(variant: FanVariant) -> BytesIO:
    hujjat = DocxTemplate(SABLON_YOLI)
    hujjat.render(dastur_kontekst(variant))
    buffer = BytesIO()
    hujjat.save(buffer)
    buffer.seek(0)
    return buffer
