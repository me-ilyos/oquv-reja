from django.urls import path

from web.views.kafedra.dashboard import KafedraDashboardView
from web.views.kafedra.yuklama import (
    TaqsimotPanelView,
    YuklamaOchirishView,
    YuklamaYaratishView,
)

urlpatterns = [
    path("", KafedraDashboardView.as_view(), name="dashboard"),
    path(
        "fan-semestr/<int:pk>/panel/",
        TaqsimotPanelView.as_view(),
        name="taqsimot_panel",
    ),
    path(
        "fan-semestr/<int:pk>/maruza/",
        YuklamaYaratishView.as_view(shakl="maruza"),
        name="maruza_yaratish",
    ),
    path(
        "fan-semestr/<int:pk>/guruh/",
        YuklamaYaratishView.as_view(shakl="guruh"),
        name="guruh_yaratish",
    ),
    path(
        "fan-semestr/<int:pk>/kurs-ishi/",
        YuklamaYaratishView.as_view(shakl="kurs_ishi"),
        name="kurs_ishi_yaratish",
    ),
    path(
        "yuklama/<int:pk>/ochirish/",
        YuklamaOchirishView.as_view(),
        name="yuklama_ochirish",
    ),
]
