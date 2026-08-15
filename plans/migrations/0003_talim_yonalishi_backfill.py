"""Backfill TalimYonalishi from each OquvReja's existing yonalish_kodi/nomi.

New yo'nalishi rows get a placeholder ta'lim/bilim sohasi — office staff
correct the classification hierarchy afterward via admin.
"""

from django.db import migrations


def bilim_talim_yonalishlarni_toldirish(apps, schema_editor):
    OquvReja = apps.get_model("plans", "OquvReja")
    BilimSohasi = apps.get_model("plans", "BilimSohasi")
    TalimSohasi = apps.get_model("plans", "TalimSohasi")
    TalimYonalishi = apps.get_model("plans", "TalimYonalishi")

    bilim_sohasi, _ = BilimSohasi.objects.get_or_create(
        kodi="0", defaults={"nomi": "Noma'lum"}
    )
    talim_sohasi, _ = TalimSohasi.objects.get_or_create(
        kodi="0", defaults={"nomi": "Noma'lum", "bilim_sohasi": bilim_sohasi}
    )

    for reja in OquvReja.objects.all():
        yonalishi, _ = TalimYonalishi.objects.get_or_create(
            kodi=reja.yonalish_kodi,
            defaults={"nomi": reja.yonalish_nomi, "talim_sohasi": talim_sohasi},
        )
        reja.talim_yonalishi = yonalishi
        reja.save(update_fields=["talim_yonalishi"])


def teskarisiga_qaytarish(apps, schema_editor):
    OquvReja = apps.get_model("plans", "OquvReja")
    for reja in OquvReja.objects.select_related("talim_yonalishi").all():
        reja.yonalish_kodi = reja.talim_yonalishi.kodi
        reja.yonalish_nomi = reja.talim_yonalishi.nomi
        reja.save(update_fields=["yonalish_kodi", "yonalish_nomi"])


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0002_bilimsohasi_alter_oquvreja_yonalish_kodi_and_more"),
    ]

    operations = [
        migrations.RunPython(
            bilim_talim_yonalishlarni_toldirish, teskarisiga_qaytarish
        ),
    ]
