from django.urls import path

from web.views.men import MenOquvDasturView, MenYuklamalarimView

urlpatterns = [
    path("", MenYuklamalarimView.as_view(), name="yuklamalar"),
    path(
        "kurs/<int:variant_id>/dastur/",
        MenOquvDasturView.as_view(),
        name="dastur",
    ),
]
