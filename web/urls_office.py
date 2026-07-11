from django.urls import path

from web.views.office.dashboard import (
    DashboardView,
    kafedra_biriktirish,
    variant_tanlash,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("fan/<int:pk>/variant/", variant_tanlash, name="variant_tanlash"),
    path("variant/<int:pk>/kafedra/", kafedra_biriktirish, name="kafedra_biriktirish"),
]
