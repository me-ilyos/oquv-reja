from django.urls import path
from django.views.generic import TemplateView

from web.mixins import OfficeAdminTalabMixin


class PlaceholderView(OfficeAdminTalabMixin, TemplateView):
    template_name = "web/parts/tez_orada.html"


urlpatterns = [
    path("", PlaceholderView.as_view(), name="dashboard"),
]
