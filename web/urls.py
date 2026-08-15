from django.contrib.auth.views import LogoutView
from django.urls import include, path

from web.views.auth import KirishView, bosh_sahifa

urlpatterns = [
    path("", bosh_sahifa, name="bosh_sahifa"),
    path("kirish/", KirishView.as_view(), name="kirish"),
    path("chiqish/", LogoutView.as_view(), name="chiqish"),
    path("office/", include(("web.urls_office", "office"))),
    path("kafedra/", include(("web.urls_kafedra", "kafedra"))),
    path("men/", include(("web.urls_men", "men"))),
    path("dev/", include(("web.urls_dev", "dev"))),
]
