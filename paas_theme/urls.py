from django.conf.urls import url

from . import dal_views
from . import views
from . import api_views

app_name = "theme"


urlpatterns = [
    url(r"^$", views.IndexView.as_view(), name="start"),
    url(r"^imprint/$", views.ImprintView.as_view(), name="imprint"),
    url(r"^about/$", views.AboutView.as_view(), name="about"),
    url(r"^contact/$", views.ContactView.as_view(), name="contact"),
    url(r"^expert-search/$", views.PersonListView.as_view(), name="expert-search"),
    url(r"search/?$", views.SearchView.as_view(), name="search"),
    url(r"^network/?$", views.network_viz),
    url(r"^api/network/$", api_views.NetVizTheme.as_view()),
    url(
        r"^person/(?P<pk>[0-9]+)$",
        views.PersonDetailView.as_view(),
        name="person-detail",
    ),
    url(
        r"^ac/obel-person/$",
        dal_views.OeblPersons.as_view(),
        name="obel-person-autocomplete",
    ),
    url(
        r"^ac/obel-professions/$",
        dal_views.ProfessionAC.as_view(),
        name="obel-professions-autocomplete",
    ),
]
