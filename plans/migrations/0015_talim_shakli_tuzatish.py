"""Rewrite talim_shakli values left over from the "shakli" needle bug
(parser/parser.py), which matched "O'qish shakli" (Kredit-modul / kredit
tizimi / Kredit modul) instead of "Ta'lim shakli". Every affected row came
from a first sheet, whose Ta'lim shakli cell reads "kunduzgi" in all 18
sources/ files, so the intended value is always "Kunduzgi".
"""

from django.db import migrations

KANONIK_SHAKLLAR = {"kunduzgi", "kechki", "sirtqi"}


def talim_shaklini_tuzatish(apps, schema_editor):
    OquvReja = apps.get_model("plans", "OquvReja")
    skipped = []

    for reja in OquvReja.objects.all():
        shakl = (reja.talim_shakli or "").strip()
        if not shakl or shakl.casefold() in KANONIK_SHAKLLAR:
            continue

        collision = OquvReja.objects.filter(
            yonalish_kodi=reja.yonalish_kodi,
            boshlanish_yili=reja.boshlanish_yili,
            talim_shakli="Kunduzgi",
        ).exclude(pk=reja.pk)
        if collision.exists():
            skipped.append((reja.pk, reja.yonalish_kodi, reja.boshlanish_yili, shakl))
            continue

        reja.talim_shakli = "Kunduzgi"
        reja.save(update_fields=["talim_shakli"])

    if skipped:
        print(
            "\n"
            f"talim_shakli_tuzatish: {len(skipped)} ta OquvReja qatori "
            "uniq_reja_kod_yil_shakl bilan to'qnashgani uchun o'zgartirilmadi:"
        )
        for pk, kod, yil, shakl in skipped:
            print(f"  pk={pk} yonalish_kodi={kod} yili={yil} talim_shakli={shakl!r}")


def teskarisiga_qaytarish(apps, schema_editor):
    # The original bad string ("Kredit-modul" / "kredit tizimi" / "Kredit
    # modul") isn't recoverable per-row, so reversal is a no-op.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0014_dastur_topshirish_tarixi"),
    ]

    operations = [
        migrations.RunPython(talim_shaklini_tuzatish, teskarisiga_qaytarish),
    ]
