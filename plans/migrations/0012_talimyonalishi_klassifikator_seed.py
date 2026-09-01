from django.db import migrations

# Official classifier rows, transcribed from the AOH's reference table.
KLASSIFIKATOR = [
    {
        "kodi": "60110200",
        "nomi": "Maktabgacha ta'lim",
        "bilim_sohasi_kodi": "100000",
        "bilim_sohasi_nomi": "Ta'lim",
        "talim_sohasi_kodi": "110000",
        "talim_sohasi_nomi": "Ta'lim",
    },
    {
        "kodi": "60110400",
        "nomi": "Boshlang'ich ta'lim",
        "bilim_sohasi_kodi": "100000",
        "bilim_sohasi_nomi": "Ta'lim",
        "talim_sohasi_kodi": "110000",
        "talim_sohasi_nomi": "Ta'lim",
    },
    {
        "kodi": "60110700",
        "nomi": "O'zbek tili va adabiyoti",
        "bilim_sohasi_kodi": "100000",
        "bilim_sohasi_nomi": "Ta'lim",
        "talim_sohasi_kodi": "110000",
        "talim_sohasi_nomi": "Ta'lim",
    },
    {
        "kodi": "60110800",
        "nomi": "Ona tili va adabiyoti (Rus)",
        "bilim_sohasi_kodi": "100000",
        "bilim_sohasi_nomi": "Ta'lim",
        "talim_sohasi_kodi": "110000",
        "talim_sohasi_nomi": "Ta'lim",
    },
    {
        "kodi": "60110900",
        "nomi": "Xorijiy til va adabiyoti (Ingliz tili)",
        "bilim_sohasi_kodi": "100000",
        "bilim_sohasi_nomi": "Ta'lim",
        "talim_sohasi_kodi": "110000",
        "talim_sohasi_nomi": "Ta'lim",
    },
    {
        "kodi": "60111200",
        "nomi": "Jismoniy madaniyat",
        "bilim_sohasi_kodi": "100000",
        "bilim_sohasi_nomi": "Ta'lim",
        "talim_sohasi_kodi": "110000",
        "talim_sohasi_nomi": "Ta'lim",
    },
    {
        "kodi": "60220300",
        "nomi": "Tarix",
        "bilim_sohasi_kodi": "200000",
        "bilim_sohasi_nomi": "San'at va gumanitar fanlar",
        "talim_sohasi_kodi": "220000",
        "talim_sohasi_nomi": "Gumanitar fanlar (tillardan tashqari)",
    },
    {
        "kodi": "60230100",
        "nomi": "Filologiya va tillarni o'qitish (O'zbek tili)",
        "bilim_sohasi_kodi": "200000",
        "bilim_sohasi_nomi": "San'at va gumanitar fanlar",
        "talim_sohasi_kodi": "230000",
        "talim_sohasi_nomi": "Tillar",
    },
    {
        "kodi": "60310200",
        "nomi": "Xalqaro munosabatlar",
        "bilim_sohasi_kodi": "300000",
        "bilim_sohasi_nomi": "Ijtimoiy fanlar, jurnalistika va axborot",
        "talim_sohasi_kodi": "310000",
        "talim_sohasi_nomi": "Ijtimoiy va xulq-atvorga mansub fanlar",
    },
    {
        "kodi": "60310300",
        "nomi": "Psixologiya",
        "bilim_sohasi_kodi": "300000",
        "bilim_sohasi_nomi": "Ijtimoiy fanlar, jurnalistika va axborot",
        "talim_sohasi_kodi": "310000",
        "talim_sohasi_nomi": "Ijtimoiy va xulq-atvorga mansub fanlar",
    },
    {
        "kodi": "60410100",
        "nomi": "Iqtisodiyot",
        "bilim_sohasi_kodi": "400000",
        "bilim_sohasi_nomi": "Biznes, boshqaruv va huquq",
        "talim_sohasi_kodi": "410000",
        "talim_sohasi_nomi": "Biznes va boshqaruv",
    },
    {
        "kodi": "60410200",
        "nomi": "Buxgalteriya hisobi",
        "bilim_sohasi_kodi": "400000",
        "bilim_sohasi_nomi": "Biznes, boshqaruv va huquq",
        "talim_sohasi_kodi": "410000",
        "talim_sohasi_nomi": "Biznes va boshqaruv",
    },
    {
        "kodi": "60410500",
        "nomi": "Moliya va moliyaviy texnologiyalar",
        "bilim_sohasi_kodi": "400000",
        "bilim_sohasi_nomi": "Biznes, boshqaruv va huquq",
        "talim_sohasi_kodi": "410000",
        "talim_sohasi_nomi": "Biznes va boshqaruv",
    },
    {
        "kodi": "60411100",
        "nomi": "Jahon iqtisodiyoti va xalqaro iqtisodiy munosabatlar",
        "bilim_sohasi_kodi": "400000",
        "bilim_sohasi_nomi": "Biznes, boshqaruv va huquq",
        "talim_sohasi_kodi": "410000",
        "talim_sohasi_nomi": "Biznes va boshqaruv",
    },
    {
        "kodi": "60510100",
        "nomi": "Biologiya",
        "bilim_sohasi_kodi": "500000",
        "bilim_sohasi_nomi": "Tabiiy fanlar, matematika va statistika",
        "talim_sohasi_kodi": "510000",
        "talim_sohasi_nomi": "Biologik va turdosh fanlar",
    },
    {
        "kodi": "60540100",
        "nomi": "Matematika",
        "bilim_sohasi_kodi": "500000",
        "bilim_sohasi_nomi": "Tabiiy fanlar, matematika va statistika",
        "talim_sohasi_kodi": "540000",
        "talim_sohasi_nomi": "Matematika va statistika",
    },
    {
        "kodi": "60610100",
        "nomi": "Axborot tizimlari va texnologiyalari",
        "bilim_sohasi_kodi": "600000",
        "bilim_sohasi_nomi": "Axborot-kommunikatsiya texnologiyalari",
        "talim_sohasi_kodi": "610000",
        "talim_sohasi_nomi": "Axborot-kommunikatsiya texnologiyalari",
    },
    {
        "kodi": "61010400",
        "nomi": "Logistika",
        "bilim_sohasi_kodi": "1000000",
        "bilim_sohasi_nomi": "Xizmatlar",
        "talim_sohasi_kodi": "1010000",
        "talim_sohasi_nomi": "Xizmat ko'rsatish sohasi",
    },
]


def seed(apps, schema_editor):
    TalimYonalishi = apps.get_model("plans", "TalimYonalishi")
    for row in KLASSIFIKATOR:
        TalimYonalishi.objects.update_or_create(kodi=row["kodi"], defaults=row)


def unseed(apps, schema_editor):
    TalimYonalishi = apps.get_model("plans", "TalimYonalishi")
    TalimYonalishi.objects.filter(
        kodi__in=[row["kodi"] for row in KLASSIFIKATOR]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0011_talimyonalishi"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
