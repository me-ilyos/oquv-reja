import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0013_dasturtopshirish"),
    ]

    operations = [
        migrations.AddField(
            model_name="dasturtopshirish",
            name="urinish_raqami",
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="dasturtopshirish",
            name="variant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dastur_topshirishlari",
                to="plans.fanvariant",
            ),
        ),
    ]
