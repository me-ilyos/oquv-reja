from django.urls import path

from web.views.men import MenYuklamalarimView

urlpatterns = [
    path("", MenYuklamalarimView.as_view(), name="yuklamalar"),
]
