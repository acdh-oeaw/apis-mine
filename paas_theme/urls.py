from django.conf.urls import url

from . import dal_views
from . import views
from . import api_views
from . import autocompletes
from . import analyze_views
from . import story_views

app_name = "paas_theme"


urlpatterns = [
    url(r"^$", views.IndexView.as_view(), name="start"),
    url(r"^imprint/$", views.ImprintView.as_view(), name="imprint"),
    url(r"^about/$", views.AboutView.as_view(), name="about"),
    url(r"^contact/$", views.ContactView.as_view(), name="contact"),
    url(r"^expert-search/$", views.PersonListView.as_view(), name="expert-search"),
    url(r"search/$", views.SearchView.as_view(), name="search"),
    url(r"^institutionen/$", views.IndexInstitutionsView.as_view(), name="institutions"),
    url(r"^institutionen/search/?$", views.SearchViewInstitutions.as_view(), name="institutionssearch"),
    url(r"^network/?$", views.network_viz),
    url(r"^stories/ns-zeit/$", story_views.NationalSozialismusStory.as_view(), name="ns_zeit"),
    url(r"^stories/test/$", views.TestView.as_view(), name="test_view"),
    url(r"^api/network/$", api_views.NetVizTheme.as_view()),
    url(r"^api/egonetwork/$", api_views.EgoNetwork.as_view()),
    url(
        r"^paas/autocompletes/institution/$",
        autocompletes.PaasInstitutionAutocomplete.as_view(),
        name="paas_institution_autocomplete",
    ),
    url(
        r"^paas/autocompletes/universitaet/$",
        autocompletes.PaasInstitutionUniAutocomplete.as_view(),
        name="paas_institution_uni_autocomplete",
    ),
    url(
        r"^paas/autocompletes/universitaet_habil/$",
        autocompletes.PaasInstitutionUniHabilitationAutocomplete.as_view(),
        name="paas_institution_uni_habil_autocomplete",
    ),
    url(
        r"^paas/autocompletes/habilitation_fach/$",
        autocompletes.PaasHabilitationFachAutocomplete.as_view(),
        name="paas_institution_habil_fach_autocomplete",
    ),
    url(
        r"^paas/autocompletes/beruf/$",
        autocompletes.PaasProfessionAutocomplete.as_view(),
        name="paas_person_beruf_autocomplete",
    ),
    url(
        r"^paas/autocompletes/schule/$",
        autocompletes.PaasInstitutionSchuleAutocomplete.as_view(),
        name="paas_institution_schule_autocomplete",
    ),
    url(
        r"^paas/autocompletes/wiss_austausch/$",
        autocompletes.PaasPlaceWAustauschAutocomplete.as_view(),
        name="paas_place_wiss_austausch_autocomplete",
    ),
    url(
        r"^paas/autocompletes/place_of_birth/$",
        autocompletes.PaasPlaceBirthAutocomplete.as_view(),
        name="paas_place_of_birth_autocomplete",
    ),
    url(
        r"^paas/autocompletes/place_of_death/$",
        autocompletes.PaasPlaceDeathAutocomplete.as_view(),
        name="paas_place_of_death_autocomplete",
    ),
    url(
        r"^paas/autocompletes/position/$",
        autocompletes.PaasPersonInstitutionPositionAutocomplete.as_view(),
        name="paas_position_autocomplete",
    ),
    url(
        r"^person/(?P<pk>[0-9]+)$",
        views.PersonDetailView.as_view(),
        name="person-detail",
    ),
    url(
        r"^institution/(?P<pk>[0-9]+)$",
        views.InstitutionDetailView.as_view(),
        name="institution-detail",
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
    url(
        r"^analyze/nationalsozialismus/$",
        analyze_views.ns_view,
        name="analyze_nationalsozialismus",
    ),
    url(
        r"^analyze/api/kommissionen$",
        api_views.GetKommissionen.as_view(),
        name="get_kommissionen",
    ),
    url(
        r"^analyze/nationalsozialismus-kommissionen/$",
        analyze_views.get_nazi_kommissionen,
        name="analyze_nationalsozialismus_kommissionen",
    ),
    url(
        r"^analyze/nationalsozialismus-vorschlag/$",
        analyze_views.proposed_by_nazi,
        name="analyze_nationalsozialismus_vorschlag",
    )
]
