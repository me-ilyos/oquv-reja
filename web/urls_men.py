from django.urls import path

from web.views.men import (
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
]
