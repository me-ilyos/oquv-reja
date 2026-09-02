from django.urls import path

from web.views.men import (
    MenDasturFaylView,
    MenDasturTarixiView,
    MenDasturTopshirishView,
    MenOquvDasturView,
    MenYuklamalarimView,
)

urlpatterns = [
    path("", MenYuklamalarimView.as_view(), name="yuklamalar"),
    path(
        "kurs/<int:variant_id>/dastur/",
        MenOquvDasturView.as_view(),
        name="dastur",
    ),
    path(
        "kurs/<int:variant_id>/dastur/topshirish/",
        MenDasturTopshirishView.as_view(),
        name="dastur_topshirish",
    ),
    path(
        "kurs/<int:variant_id>/dastur/tarixi/",
        MenDasturTarixiView.as_view(),
        name="dastur_tarixi",
    ),
    path(
        "dastur/urinish/<int:pk>/fayl/",
        MenDasturFaylView.as_view(),
        name="dastur_fayl",
    ),
]
