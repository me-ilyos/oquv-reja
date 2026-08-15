from django.urls import path

from web.views.office.dashboard import (
    DashboardView,
    kafedra_biriktirish,
    variant_tanlash,
)
from web.views.office.kafedralar import (
    KafedraListView,
    KafedraTahrirView,
    KafedraYangiView,
    kafedra_mudir,
    kafedra_ochirish,
)
from web.views.office.oqituvchilar import (
    OqituvchiListView,
    OqituvchiTahrirView,
    OqituvchiYangiView,
    oqituvchi_ochirish,
)
from web.views.office.rejalar import (
    RejaDetailView,
    RejaImportView,
    RejaListView,
    RejaTahrirView,
    semestrovka_saqlash,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("fan/<int:pk>/variant/", variant_tanlash, name="variant_tanlash"),
    path("variant/<int:pk>/kafedra/", kafedra_biriktirish, name="kafedra_biriktirish"),
    path("rejalar/", RejaListView.as_view(), name="reja_list"),
    path("rejalar/yangi/", RejaImportView.as_view(), name="reja_yangi"),
    path("rejalar/<int:pk>/", RejaDetailView.as_view(), name="reja_detail"),
    path("rejalar/<int:pk>/tahrir/", RejaTahrirView.as_view(), name="reja_tahrir"),
    path(
        "rejalar/<int:pk>/semestrovka/",
        semestrovka_saqlash,
        name="semestrovka_saqlash",
    ),
    path("kafedralar/", KafedraListView.as_view(), name="kafedra_list"),
    path("kafedralar/yangi/", KafedraYangiView.as_view(), name="kafedra_yangi"),
    path(
        "kafedralar/<int:pk>/tahrir/",
        KafedraTahrirView.as_view(),
        name="kafedra_tahrir",
    ),
    path("kafedralar/<int:pk>/ochirish/", kafedra_ochirish, name="kafedra_ochirish"),
    path("kafedralar/<int:pk>/mudir/", kafedra_mudir, name="kafedra_mudir"),
    path("oqituvchilar/", OqituvchiListView.as_view(), name="oqituvchi_list"),
    path("oqituvchilar/yangi/", OqituvchiYangiView.as_view(), name="oqituvchi_yangi"),
    path(
        "oqituvchilar/<int:pk>/tahrir/",
        OqituvchiTahrirView.as_view(),
        name="oqituvchi_tahrir",
    ),
    path(
        "oqituvchilar/<int:pk>/ochirish/", oqituvchi_ochirish, name="oqituvchi_ochirish"
    ),
]
