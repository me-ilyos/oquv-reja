# Step 1/3 of collapsing BilimSohasi/TalimSohasi/TalimYonalishi into plain
# fields on OquvReja: add the new columns nullable so 0009 can backfill them.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0007_alter_oquvreja_bilim_sohasi_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="oquvreja",
            name="bilim_sohasi_kodi",
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="oquvreja",
            name="bilim_sohasi_nomi",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="oquvreja",
            name="talim_sohasi_kodi",
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="oquvreja",
            name="talim_sohasi_nomi",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="oquvreja",
            name="yonalish_kodi",
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="oquvreja",
            name="yonalish_nomi",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
