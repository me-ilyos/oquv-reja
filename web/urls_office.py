from django.urls import path

from web.views.office.dashboard import (
    DashboardView,
    kafedra_biriktirish,
    variant_tanlash,
)
from web.views.office.rejalar import (
    RejaDetailView,
    RejaImportView,
    RejaListView,
    RejaTahrirView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("fan/<int:pk>/variant/", variant_tanlash, name="variant_tanlash"),
    path("variant/<int:pk>/kafedra/", kafedra_biriktirish, name="kafedra_biriktirish"),
    path("rejalar/", RejaListView.as_view(), name="reja_list"),
    path("rejalar/yangi/", RejaImportView.as_view(), name="reja_yangi"),
    path("rejalar/<int:pk>/", RejaDetailView.as_view(), name="reja_detail"),
    path("rejalar/<int:pk>/tahrir/", RejaTahrirView.as_view(), name="reja_tahrir"),
]
