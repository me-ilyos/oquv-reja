"""Submission and AOH review of the O'quv Dastur a teacher fills in and
sends back. Sibling module to `plans/dastur/service.py` (generation) — one
module per responsibility.
"""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from accounts.models import Foydalanuvchi, OqituvchiProfil
from plans.dastur.service import dastur_egasimi
from plans.models import DasturTopshirish, FanVariant, TopshirishHolati


def dastur_topshirish(
    variant: FanVariant, oqituvchi: OqituvchiProfil, fayl: UploadedFile
) -> DasturTopshirish:
    """Create or overwrite this variant's submission; only the lecture owner may."""
    if not dastur_egasimi(variant, oqituvchi):
        raise ValidationError(
            "Bu fan dasturini faqat ma'ruza egasi topshirishi mumkin."
        )
    topshirish, yaratildimi = DasturTopshirish.objects.get_or_create(
        variant=variant,
        defaults={"oqituvchi": oqituvchi, "fayl": fayl},
    )
    if not yaratildimi:
        topshirish.fayl.delete(save=False)
        topshirish.oqituvchi = oqituvchi
        topshirish.fayl = fayl
    topshirish.holat = TopshirishHolati.KUTILMOQDA
    topshirish.izoh = ""
    topshirish.yuborilgan_vaqt = timezone.now()
    topshirish.korib_chiqilgan_vaqt = None
    topshirish.korib_chiqqan = None
    topshirish.save()
    return topshirish


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
