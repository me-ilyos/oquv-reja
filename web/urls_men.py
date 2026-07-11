from django.urls import path
from django.views.generic import TemplateView

from web.mixins import OqituvchiTalabMixin


class PlaceholderView(OqituvchiTalabMixin, TemplateView):
    template_name = "web/parts/tez_orada.html"


urlpatterns = [
    path("", PlaceholderView.as_view(), name="yuklamalar"),
]
