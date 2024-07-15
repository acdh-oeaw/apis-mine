from django.urls import path
from . import dal_views
from . import views
from . import api_views
from . import autocompletes
from . import analyze_views
from . import story_views

app_name = "paas_theme"


urlpatterns = [
    path("", views.IndexView.as_view(), name="start"),
    path(r"imprint/", views.ImprintView.as_view(), name="imprint"),
    path(r"about/", views.AboutView.as_view(), name="about"),
    path(r"contact/", views.ContactView.as_view(), name="contact"),
    path(r"expert-search/", views.PersonListView.as_view(), name="expert-search"),
    path(r"search/", views.SearchView.as_view(), name="search"),
    path(r"institutionen/", views.IndexInstitutionsView.as_view(), name="institutions"),
    path(r"institutionen/search/", views.SearchViewInstitutions.as_view(), name="institutionssearch"),
    path(r"network/", views.network_viz),
    path(r"stories/ns-zeit/", story_views.NationalSozialismusStory.as_view(), name="ns_zeit"),
    path(r"stories/test/", views.TestView.as_view(), name="test_view"),
    path(r"stories/", views.StoriesIndexPage.as_view(), name="stories_index"),
    path(r"api/network/", api_views.NetVizTheme.as_view()),
    path(r"api/egonetwork/", api_views.EgoNetwork.as_view()),
    path(r"api/lifepath/<int:pk>/", api_views.LifePathMINEViewset.as_view()),
    path(
        "paas/autocompletes/person/",
        autocompletes.PaasPersonAutocomplete.as_view(),
        name="paas_person_autocomplete",
    ),
    path(
        "paas/autocompletes/preise/",
        autocompletes.PaasPreiseAutocomplete.as_view(),
        name="paas_preise_autocomplete",
    ),
    path(
        r"paas/autocompletes/institution/",
        autocompletes.PaasInstitutionAutocomplete.as_view(),
        name="paas_institution_autocomplete",
    ),
    path(
        r"paas/autocompletes/universitaet/",
        autocompletes.PaasInstitutionUniAutocomplete.as_view(),
        name="paas_institution_uni_autocomplete",
    ),
    path(
        r"paas/autocompletes/universitaet_habil/",
        autocompletes.PaasInstitutionUniHabilitationAutocomplete.as_view(),
        name="paas_institution_uni_habil_autocomplete",
    ),
    path(
        r"paas/autocompletes/habilitation_fach/",
        autocompletes.PaasHabilitationFachAutocomplete.as_view(),
        name="paas_institution_habil_fach_autocomplete",
    ),
    path(
        r"paas/autocompletes/beruf/",
        autocompletes.PaasProfessionAutocomplete.as_view(),
        name="paas_person_beruf_autocomplete",
    ),
    path(
        r"paas/autocompletes/schule/",
        autocompletes.PaasInstitutionSchuleAutocomplete.as_view(),
        name="paas_institution_schule_autocomplete",
    ),
    path(
        r"paas/autocompletes/wiss_austausch/",
        autocompletes.PaasPlaceWAustauschAutocomplete.as_view(),
        name="paas_place_wiss_austausch_autocomplete",
    ),
    path(
        r"paas/autocompletes/place_of_birth/",
        autocompletes.PaasPlaceBirthAutocomplete.as_view(),
        name="paas_place_of_birth_autocomplete",
    ),
    path(
        r"paas/autocompletes/place_of_death/",
        autocompletes.PaasPlaceDeathAutocomplete.as_view(),
        name="paas_place_of_death_autocomplete",
    ),
    path(
        r"paas/autocompletes/position/",
        autocompletes.PaasPersonInstitutionPositionAutocomplete.as_view(),
        name="paas_position_autocomplete",
    ),
    path(
        r"person/<int:pk>",
        views.PersonDetailView.as_view(),
        name="person-detail",
    ),
    path(
            r"institution/<int:pk>",
        views.InstitutionDetailView.as_view(),
        name="institution-detail",
    ),
    path(
        r"ac/obel-person/",
        dal_views.OeblPersons.as_view(),
        name="obel-person-autocomplete",
    ),
    path(
        r"ac/obel-professions/",
        dal_views.ProfessionAC.as_view(),
        name="obel-professions-autocomplete",
    ),
    path(
        r"analyze/nationalsozialismus/",
        analyze_views.ns_view,
        name="analyze_nationalsozialismus",
    ),
    path(
        r"analyze/api/kommissionen",
        api_views.GetKommissionen.as_view(),
        name="get_kommissionen",
    ),
    path(
        r"analyze/nationalsozialismus-kommissionen/",
        analyze_views.get_nazi_kommissionen,
        name="analyze_nationalsozialismus_kommissionen",
    ),
    path(
        r"analyze/nationalsozialismus-vorschlag/",
        analyze_views.proposed_by_nazi,
        name="analyze_nationalsozialismus_vorschlag",
    ),
    path(
        r"analyze/mitglieder/",
        analyze_views.mitglieder,
        name="mitglieder",
    )
]
