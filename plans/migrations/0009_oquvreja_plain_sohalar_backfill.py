# Step 2/3: copy each OquvReja's classification chain (bilim_sohasi ->
# talim_sohasi -> talim_yonalishi) into the new plain kodi/nomi fields.

from django.db import migrations


def sohalarni_tekislash(apps, schema_editor):
    OquvReja = apps.get_model("plans", "OquvReja")
    for reja in OquvReja.objects.select_related(
        "bilim_sohasi", "talim_sohasi", "talim_yonalishi"
    ):
        reja.bilim_sohasi_kodi = reja.bilim_sohasi.kodi
        reja.bilim_sohasi_nomi = reja.bilim_sohasi.nomi
        reja.talim_sohasi_kodi = reja.talim_sohasi.kodi
        reja.talim_sohasi_nomi = reja.talim_sohasi.nomi
        reja.yonalish_kodi = reja.talim_yonalishi.kodi
        reja.yonalish_nomi = reja.talim_yonalishi.nomi
        reja.save(
            update_fields=[
                "bilim_sohasi_kodi",
                "bilim_sohasi_nomi",
                "talim_sohasi_kodi",
                "talim_sohasi_nomi",
                "yonalish_kodi",
                "yonalish_nomi",
            ]
        )


def teskarisiga_qaytarish(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0008_oquvreja_add_plain_sohalar"),
    ]

    operations = [
        migrations.RunPython(sohalarni_tekislash, teskarisiga_qaytarish),
    ]
