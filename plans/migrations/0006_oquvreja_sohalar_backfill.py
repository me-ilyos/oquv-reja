"""Backfill OquvReja.bilim_sohasi/talim_sohasi from its talim_yonalishi chain.

Both fields are now direct, independent hooks on OquvReja rather than only
reachable via talim_yonalishi.talim_sohasi.bilim_sohasi.
"""

from django.db import migrations


def sohalarni_toldirish(apps, schema_editor):
    OquvReja = apps.get_model("plans", "OquvReja")
    for reja in OquvReja.objects.select_related(
        "talim_yonalishi__talim_sohasi__bilim_sohasi"
    ):
        talim_sohasi = reja.talim_yonalishi.talim_sohasi
        reja.talim_sohasi = talim_sohasi
        reja.bilim_sohasi = talim_sohasi.bilim_sohasi
        reja.save(update_fields=["bilim_sohasi", "talim_sohasi"])


def teskarisiga_qaytarish(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0005_oquvreja_bilim_sohasi_oquvreja_talim_sohasi"),
    ]

    operations = [
        migrations.RunPython(sohalarni_toldirish, teskarisiga_qaytarish),
    ]
