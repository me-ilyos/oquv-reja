# Step 3/3: remove the FK fields and the now-empty lookup models, tighten the
# new plain fields to non-null, and restore the unique constraint keyed on
# the plain yonalish_kodi (mirrors the pre-0002 schema).

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0009_oquvreja_plain_sohalar_backfill"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="oquvreja",
            name="uniq_reja_kod_yil_shakl",
        ),
        migrations.RemoveField(
            model_name="oquvreja",
            name="bilim_sohasi",
        ),
        migrations.RemoveField(
            model_name="oquvreja",
            name="talim_sohasi",
        ),
        migrations.RemoveField(
            model_name="oquvreja",
            name="talim_yonalishi",
        ),
        migrations.AlterField(
            model_name="oquvreja",
            name="bilim_sohasi_kodi",
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name="oquvreja",
            name="bilim_sohasi_nomi",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="oquvreja",
            name="talim_sohasi_kodi",
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name="oquvreja",
            name="talim_sohasi_nomi",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="oquvreja",
            name="yonalish_kodi",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name="oquvreja",
            name="yonalish_nomi",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddConstraint(
            model_name="oquvreja",
            constraint=models.UniqueConstraint(
                fields=("yonalish_kodi", "boshlanish_yili", "talim_shakli"),
                name="uniq_reja_kod_yil_shakl",
            ),
        ),
        migrations.DeleteModel(name="TalimYonalishi"),
        migrations.DeleteModel(name="TalimSohasi"),
        migrations.DeleteModel(name="BilimSohasi"),
    ]
