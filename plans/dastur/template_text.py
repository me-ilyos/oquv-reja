"""Static Uzbek prose for the o'quv dastur template: grading rubric, teaching
methods, and reference citations. Kept separate from build_template.py so
text-only fixes are a one-line diff and table-construction code stays under
the ~40-line function limit.
"""

IZOH = (
    "Izoh: Fan (modul) yuzasidan talabalar bajaradigan mustaqil ish "
    "topshiriqlari variativ tavsifga ega bo‘lishi lozim. Mustaqil ish "
    "topshiriqlarining 1/3 qismi kichik guruhlarda hamkorlikda ishlash "
    "(kooperativlik)ga mo‘ljallangan bo‘lishi kerak."
)

TEACHING_METHODS_BULLETS = [
    "Ma’ruzalar;",
    "interfaol keys-studylar;",
    "amaliy mashg‘ulotlar;",
    "guruhlarda ishlash;",
    "taqdimotlarni qilish;",
    "Sun’iy intellekt (AI) vositalaridan ta’lim jarayonida maqsadli va "
    "mas’uliyatli foydalanish:",
    " AI vositalari yordamida axborotni izlash, saralash;",
    "        AI vositalaridan foydalanishda akademik halollik va "
    "mualliflik huquqi talablariga rioya qilish.",
]

CREDIT_REQUIREMENTS = (
    "Fanga oid nazariy va uslubiy tushunchalarni to‘la o‘zlashtirish, "
    "tahlil natijalarini to‘g‘ri aks ettira olish, o‘rganilayotgan "
    "jarayonlar haqida mustaqil mushohada yuritish va nazorat uchun "
    "berilgan vazifa va topshiriqlarni bajarish, yakuniy nazorat bo‘yicha "
    "test topshiriqlarini bajarish."
)

# Each item: (text, bold, alignment) where alignment is "justify" or "center".
GRADING_POLICY_PARAGRAPHS = [
    (
        "Fandan talabalarni bilimini baholash uchun 5 (100 ball) baholik  "
        "tizimda baholanadi. Nazorat turlari  ON va YN turlariga "
        "bo‘linadi. ON  uchun eng yuqori baho 5 (50 ball), saralash baho "
        "esa 3 (30 ball). YN uchun eng yuqori baho 5 (50 ball) saralash  "
        "baho esa 3 (30 ball). Oraliq nazorat turi har bir fan bo‘yicha "
        "fanning xususiyatidan kelib chiqqan holda 2 martagacha "
        "o‘tkazilishi mumkin. Oraliq nazorat turini o‘tkazish shakli va "
        "muddati fanning xususiyati va fanga ajratilgan soatlardan kelib "
        "chiqib tegishli kafedra tomonidan belgilanadi. Semestr davomida "
        "haftasiga 2 akademik soatdan kam bo‘lgan fanlar bo‘yicha oraliq "
        "nazorat turi o‘tkazilmaydi.",
        False,
        "justify",
    ),
    ("ORALIQ NAZORAT TAQSIMOTI", True, "center"),
    ("", False, "justify"),
    (
        "Oraliq nazorat topshiriqlari fanning talaba tomonidan mustaqil "
        "o‘zlashtirishi lozim bo‘lgan qismi bo‘yicha shakllantiriladi. ",
        False,
        "justify",
    ),
    ("Baholash mezonlari", True, "center"),
    (
        "Tartibga ko‘ra, baholash quyidagi 4 ta mezonning "
        "integratsiyasidan tashkil topadi:",
        False,
        "center",
    ),
    ("", False, "center"),
    (
        "       1-ON ni topshirish muddati 2-ON haftaligi boshlangunga,  "
        "2-ON ni topshirish muddati YaN boshlangunga  qadar etib "
        "belgilanadi.",
        False,
        "justify",
    ),
    (
        "       ON lardan kamida 3 baho to‘plagan talabaga YaN uchun ruxsat etiladi.",
        False,
        "justify",
    ),
    (
        "       YN da talabaga barcha mavzularga oid test beriladi va "
        "test savollari soni 30 ta bo‘lib: ",
        False,
        "justify",
    ),
    (
        "             17-22 tа savolga to‘g‘ri javob bersa 3 baho; ",
        False,
        "justify",
    ),
    (
        "             23-26 ta savolga to‘g‘ri javob bersa 4 baho;",
        False,
        "justify",
    ),
    (
        "             27-30 ta savolga to‘g‘ri javob bersa 5 baho qo‘yiladi.",
        False,
        "justify",
    ),
    ("         ", False, "justify"),
    (
        "           Fanga ajratilgan auditoriya soatining 25 foizini va "
        "undan ortiq soatni sababsiz qoldirgan talaba ushbu fandan "
        "chetlashtirilib, yakuniy nazoratga kiritilmaydi hamda mazkur fan "
        "bo‘yicha tegishli kreditlarni o‘zlashtirmagan hisoblanadi.",
        False,
        "justify",
    ),
    ("", False, "justify"),
    (
        "a) 5 baho olish uchun talabaning bilim darajasi quyidagilarga "
        "javob berishi lozim:",
        True,
        "justify",
    ),
    ("fanning mohiyati va mazmunini to‘liq yorita olsa;", False, "justify"),
    (
        "fandagi mavzularni bayon qilishda ilmiylik va mantiqiylik "
        "saqlanib, ilmiy xatolik va chalkashliklarga yo‘l qo‘ymasa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha mavzu materiallarining nazariy yoki amaliy "
        "ahamiyati haqida aniq tasavvurga ega bo‘lsa;",
        False,
        "justify",
    ),
    (
        "fan doirasida mustaqil erkin fikrlash qobiliyatini namoyon eta olsa;",
        False,
        "justify",
    ),
    ("berilgan savollarga aniq va lo‘nda javob bera olsa;", False, "justify"),
    ("konspektga puxta tayyorlangan bo‘lsa;", False, "justify"),
    (
        "mustaqil topshiriqlarni to‘liq va aniq bajargan bo‘lsa;",
        False,
        "justify",
    ),
    (
        "barcha amaliy ko‘nikma va malakalarni o‘zlashtirgan bo‘lsa;",
        False,
        "justify",
    ),
    ("nazariy bilimlarni turli vaziyatda qo‘llash olish;", False, "justify"),
    ("tizimli yondashish, uzviylikka amal qilish.", False, "justify"),
    (
        "b) 4 baho olish uchun talabaning bilim darajasi quyidagilarga "
        "javob berishi lozim:",
        True,
        "justify",
    ),
    (
        "fanning mohiyati va mazmunini tushungan, fandagi mavzularni "
        "bayon qilishda ilmiy va mantiqiy chalkashliklarga yo‘l qo‘ymasa;",
        False,
        "justify",
    ),
    (
        "fanning mazmunini amaliy ahamiyatini tushungan bo‘lsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha berilgan vazifa va topshiriqlarni o‘quv dasturi "
        "doirasida bajarsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha berilgan savollarga to‘g‘ri javob bera olsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha konspektini puxta shakllantirgan bo‘lsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha mustaqil topshiriqlarni to‘liq bajargan bo‘lsa;",
        False,
        "justify",
    ),
    (
        "barcha amaliy ko‘nikma va malakalarni o‘zlashtirishga harakat qilgan bo‘lsa.",
        False,
        "justify",
    ),
    (
        "d) 3 baho olish uchun talabaning bilim darajasi quyidagilarga "
        "javob berishi lozim:",
        True,
        "justify",
    ),
    ("fan haqida umumiy tushunchaga ega bo‘lsa;", False, "justify"),
    (
        "fandagi mavzularni tor doirada yoritib, bayon qilishda ayrim "
        "chalkashliklarga yo‘l qo‘yilsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha mustaqil topshiriqlarni to‘liq bajargan bo‘lsa;",
        False,
        "justify",
    ),
    ("bayon qilish ravon bo‘lmasa;", False, "justify"),
    (
        "fan bo‘yicha savollarga mujmal va chalkash javoblar olinsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha matn puxta shakllantirilmagan bo‘lsa.",
        False,
        "justify",
    ),
    (
        "e) quyidagi hollarda talabaning bilim darajasi qoniqarsiz 2 "
        "baho bilan baholanishi mumkin:",
        True,
        "justify",
    ),
    (
        "fan bo‘yicha mashg‘ulotlarga tayyorgarlik ko‘rilmagan bo‘lsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha mashg‘ulotlarga doir hech qanday tasavvurga ega bo‘lmasa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha mustaqil topshiriqlarni to‘liq bajarmagan bo‘lsa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha matnlarni boshqalardan ko‘chirib olganligi sezilib tursa;",
        False,
        "justify",
    ),
    (
        "fan bo‘yicha matnda jiddiy xato va chalkashliklarga yo‘l qo‘yilgan bo‘lsa;",
        False,
        "justify",
    ),
    ("fanga doir berilgan savollarga javob olinmasa;", False, "justify"),
    ("fanni bilmasa.", False, "justify"),
]

# Each item: (number, citation_text, url_or_None).
ASOSIY_ADABIYOTLAR = [
    (
        "1",
        "Aminov M.,Madvaliyev A., Mahkamov N., Mahmudov N., Odilov Y. "
        "Davlat tilida ish yuritish. Amaliy qo‘llanma. – Toshkent: "
        "O‘zbekiston, 2020.",
        None,
    ),
    (
        "2",
        "Yokubbayeva U. Akademik yozuv: Oʻquv qoʻllanma. – Namangan: "
        "Sunrise-pro, 2026. – 176 b.",
        None,
    ),
]

QOSHIMCHA_ADABIYOTLAR = [
    (
        "1",
        "Husanov N.A, Xo‘jaqulova R.Sh. Biznes muloqot va akademik "
        "yozuv. – Toshkent: Iqtisod-moliya, 2019.",
        None,
    ),
    (
        "2",
        "Hayot, Erik (2014). Akademik uslubning elementlari: Gumanitar "
        "fanlar uchun yozish.Kolumbiya universiteti matbuoti. ISBN "
        "978-0-231-53741-4",
        None,
    ),
]

AXBOROT_MANBALARI = [
    ("1", "www.lex.uz ", None),
    ("2", "www.pedagogika.uz", "http://www.pedagogika.uz"),
    ("3", "www.ziyonet.uz  ", "http://www.ziyonet.uz"),
]
