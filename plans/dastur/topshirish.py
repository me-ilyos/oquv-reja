"""Submission and AOH review of the O'quv Dastur a teacher fills in and
sends back. Sibling module to `plans/dastur/service.py` (generation) — one
module per responsibility.
"""

import itertools

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from django.utils import timezone

from accounts.models import Foydalanuvchi, OqituvchiProfil
from plans.dastur.service import dastur_egasimi
from plans.models import DasturTopshirish, FanVariant, TopshirishHolati


def dastur_topshirish(
    variant: FanVariant, oqituvchi: OqituvchiProfil, fayl: UploadedFile
) -> DasturTopshirish:
    """Record a new submission attempt; only the lecture owner may submit.

    Past attempts are never touched — each resubmission is a new row, so
    earlier rejection reasons stay intact for both sides to review.
    """
    if not dastur_egasimi(variant, oqituvchi):
        raise ValidationError(
            "Bu fan dasturini faqat ma'ruza egasi topshirishi mumkin."
        )
    oldingi = eng_songi_urinish(variant)
    if oldingi is not None and oldingi.holat == TopshirishHolati.KUTILMOQDA:
        raise ValidationError(
            "Joriy topshiriq hali ko'rib chiqilmoqda — javob kutilsin."
        )
    return DasturTopshirish.objects.create(
        variant=variant,
        urinish_raqami=(oldingi.urinish_raqami + 1 if oldingi else 1),
        oqituvchi=oqituvchi,
        fayl=fayl,
        holat=TopshirishHolati.KUTILMOQDA,
        yuborilgan_vaqt=timezone.now(),
    )


def dastur_qabul_qilish(topshirish: DasturTopshirish, admin: Foydalanuvchi) -> None:
    topshirish.holat = TopshirishHolati.QABUL_QILINDI
    topshirish.korib_chiqilgan_vaqt = timezone.now()
    topshirish.korib_chiqqan = admin
    topshirish.save(update_fields=["holat", "korib_chiqilgan_vaqt", "korib_chiqqan"])


def dastur_rad_etish(
    topshirish: DasturTopshirish, admin: Foydalanuvchi, izoh: str
) -> None:
    if not izoh.strip():
        raise ValidationError("Rad etish sababi ko'rsatilishi shart.")
    topshirish.holat = TopshirishHolati.RAD_ETILDI
    topshirish.izoh = izoh
    topshirish.korib_chiqilgan_vaqt = timezone.now()
    topshirish.korib_chiqqan = admin
    topshirish.save(
        update_fields=["holat", "izoh", "korib_chiqilgan_vaqt", "korib_chiqqan"]
    )


def eng_songi_urinish(variant: FanVariant) -> DasturTopshirish | None:
    """Latest submission attempt for `variant`, or None if never submitted."""
    return variant.dastur_topshirishlari.first()


def joriy_topshirishlar(
    qs: "QuerySet[DasturTopshirish] | None" = None,
) -> list[DasturTopshirish]:
    """One row per variant — its latest attempt only — for the AOH list page.

    Groups in Python rather than `QuerySet.distinct(*fields)`, which is
    Postgres-only and this project's DB backend isn't guaranteed to be
    Postgres.
    """
    if qs is None:
        qs = DasturTopshirish.objects.all()
    qs = qs.order_by("variant_id", "-yuborilgan_vaqt")
    return [
        next(urinishlar)
        for _, urinishlar in itertools.groupby(qs, key=lambda t: t.variant_id)
    ]
