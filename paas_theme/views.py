import random
from typing import Any, Dict

import requests
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import UserPassesTestMixin


from apis_core.apis_entities.models import Person
from apis_core.apis_entities.models import Institution
from apis_core.apis_relations.models import PersonPlace
from apis_core.apis_entities.views import set_session_variables
from browsing.browsing_utils import GenericListView
from paas_theme.models import PAASInstitution
from webpage.views import get_imprint_url
from .filters import PersonListFilter
from .forms import (
    PersonFilterFormHelper,
    PersonFacetedSearchForm,
    PersonFacetedSearchFormNew,
    InstitutionFacetedSearchForm,
    InstitutionFacetedSearchFormNew,
)
from .tables import PersonTable, SearchResultTable, InstitutionTable, InstitutionsSearchResultTable
from .provide_data import oebl_persons, institutions, enrich_person_context, enrich_institution_context, classes

from apis_core.helper_functions.utils import access_for_all

from haystack.generic_views import FacetedSearchView
from haystack.forms import FacetedSearchForm
from haystack.query import SearchQuerySet
from haystack.query import RelatedSearchQuerySet
from haystack.models import SearchResult

# from django.shortcuts import render_to_response
from django.shortcuts import render

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from django_tables2.config import RequestConfig
from django.conf import settings


class ImprintView(TemplateView):
    template_name = "theme/imprint.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        imprint_url = get_imprint_url()
        r = requests.get(get_imprint_url())

        if r.status_code == 200:
            context["imprint_body"] = "{}".format(r.text)
        else:
            context[
                "imprint_body"
            ] = """
            On of our services is currently not available. Please try it later or write an email to
            acdh@oeaw.ac.at; if you are service provide, make sure that you provided
            ACDH_IMPRINT_URL and REDMINE_ID
            """
        return context


class IndexView(TemplateView):
    model = Person
    template_name = "theme/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Mitglieder der Österreichischen Akademie der Wissenschaften"
        context["intro_text"] = "Die Österreichische Akademie der Wissenschaften besteht aus zwei Klassen, der mathematisch-naturwissenschaftlichen und der philosophisch-historischen Klasse. Die Gelehrtengesellschaft ergänzt sich selbst durch die Wahl neuer Mitglieder."
        context["search_form"] = PersonFacetedSearchFormNew()
        return context

class IndexInstitutionsView(TemplateView):
    model = Institution
    template_name = "theme/institutions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Institutionen der Österreichischen Akademie der Wissenschaften"
        context["intro_text"] = "Die Österreichische Akademie der Wissenschaften organisiert ihre Forschungstätigkeit in Kommissionen und Instituten. Hier können Sie nach historischen und gegenwärtigen Forschungseinrichtungen suchen und kombinierte Auswertungen durchführen."
        context["search_form"] = InstitutionFacetedSearchFormNew()
        return context        

class StoriesIndexPage(UserPassesTestMixin, TemplateView):
    template_name = "theme/stories.html"
    login_url = "/webpage/accounts/login/"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["stories"] = getattr(settings, "PAAS_STORIES", [])
        return context

    def test_func(self):
        access = access_for_all(self, viewtype="detail")
        if access:
            self.request = set_session_variables(self.request)
        return access


class AboutView(TemplateView):
    template_name = "theme/about.html"


class ContactView(TemplateView):
    template_name = "theme/contact.html"


class TestView(TemplateView):
    template_name = "theme/test_template.html"


class PersonListView(GenericListView):
    model = Person
    filter_class = PersonListFilter
    formhelper_class = PersonFilterFormHelper
    table_class = PersonTable
    template_name = "theme/generic_list.html"
    init_columns = [
        "name",
        "first_name",
    ]

    def get_queryset(self, **kwargs):
        self.filter = self.filter_class(self.request.GET, queryset=oebl_persons)
        self.filter.form.helper = self.formhelper_class()
        return self.filter.qs


class PersonSearchView(UserPassesTestMixin, FacetedSearchView):
    login_url = "/webpage/accounts/login/"
    queryset = SearchQuerySet()
    form_class = PersonFacetedSearchFormNew
    facet_fields = [
        # "akademiemitgliedschaft",
        "gender",
        "place_of_birth",
        "profession",
    ]
    facet_fields_optional = {"place_of_birth": ["place_of_death"]}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network_buttons"] = [
            {"key": k, "label": v["label"]}
            if "label" in v.keys()
            else {"key": k, "label": k}
            for k, v in classes["netzwerk"].items()
        ]
        context["related_institutions"] = [
            {"key": k, "label": v["label"]}
            if "label" in v.keys()
            else {"key": k, "label": k}
            for k, v in classes["linked_search_institution"].items()
        ]
        context["selected_filters"] = []
        for k, v in context["form"].cleaned_data.items():
            if v:
                if isinstance(v, list):
                    if isinstance(v[0], str):
                        kind = "boolean"
                    else:
                        kind = "multi"
                else:
                    kind = "string"
                context["selected_filters"].append(
                    {"field": k, "value": v, "kind": kind}
                )
        return context

    def get_queryset(self):
        for k, v in self.request.GET.items():
            if v != "" and k in self.facet_fields_optional.keys():
                self.facet_fields.extend(self.facet_fields_optional[k])
        qs = super().get_queryset()
        return qs

    def test_func(self):
        access = access_for_all(self, viewtype="detail")
        if access:
            self.request = set_session_variables(self.request)
        return access


class SearchView(SingleTableMixin, PersonSearchView, UserPassesTestMixin):
    table_class = SearchResultTable
    template_name = "theme/person_search.html"

    def get_table_data(self):
        return self.queryset

class InstitutionSearchView(UserPassesTestMixin, FacetedSearchView):
    login_url = "/webpage/accounts/login/"
    queryset = SearchQuerySet().models(Institution)
    form_class = InstitutionFacetedSearchFormNew
    facet_fields = [
        # "akademiemitgliedschaft",
        #"start_date",
        #"place_of_death",
        # "comissions",
        "kind",
        # "education",
        # "career",
    ]
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network_buttons"] = [
            {"key": k, "label": v["label"]}
            if "label" in v.keys()
            else {"key": k, "label": k}
            for k, v in classes["netzwerk"].items()
        ]
        return context

    def test_func(self):
        access = access_for_all(self, viewtype="detail")
        if access:
            self.request = set_session_variables(self.request)
        return access


class SearchViewInstitutions(SingleTableMixin, InstitutionSearchView, UserPassesTestMixin):
    table_class = InstitutionsSearchResultTable
    template_name = "theme/institution_search.html"

    def get_table_data(self):
        return self.queryset


class PersonDetailView(UserPassesTestMixin, DetailView):
    model = Person
    template_name = "theme/person_detail.html"
    login_url = "/webpage/accounts/login/"

    def test_func(self):
        access = access_for_all(self, viewtype="detail")
        if access:
            self.request = set_session_variables(self.request)
        return access

    def get_object(self):
        obj = Person.objects.prefetch_related(
            "personinstitution_set",
            "personinstitution_set__relation_type",
            "personinstitution_set__related_institution",
            "personplace_set",
            "personplace_set__related_place",
            "personplace_set__relation_type",
            "personevent_set",
            "personevent_set__related_event",
            "personevent_set__relation_type",
            "personwork_set",
            "personwork_set__related_work",
            "personwork_set__relation_type",
            "related_personA",
            "related_personA__related_personA",
            "related_personA__relation_type",
            "related_personB",
            "related_personB__related_personB",
            "related_personB__relation_type",
        ).get(pk=self.kwargs["pk"])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            context["prev"] = (
                oebl_persons.filter(id__lt=self.object.id).order_by("-id").first()
            )
        except AttributeError:
            context["prev"] = None
        try:
            context["next"] = oebl_persons.filter(id__gt=self.object.id).first()
        except AttributeError:
            context["next"] = None
        enriched_context = enrich_person_context(self.object, context)
        
        if self.request.GET.get('subview') == 'minimal':
            self.template_name = "theme/person_detail_popover.html"

        return enriched_context

class InstitutionDetailView(UserPassesTestMixin, DetailView):
    model = Institution
    template_name = "theme/institution_detail.html"
    login_url = "/webpage/accounts/login/"

    def test_func(self):
        access = access_for_all(self, viewtype="detail")
        if access:
            self.request = set_session_variables(self.request)
        return access

    def get_object(self):
        obj = PAASInstitution.objects.prefetch_related(
            "personinstitution_set",
            "personinstitution_set__relation_type",
            "personinstitution_set__related_institution",
        ).get(pk=self.kwargs["pk"])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            context["prev"] = (
                institutions.filter(id__lt=self.object.id).order_by("-id").first()
            )
        except AttributeError:
            context["prev"] = None
        try:
            context["next"] = institutions.filter(id__gt=self.object.id).first()
        except AttributeError:
            context["next"] = None
        #enriched_context = enrich_institution_context(self.object, context)
        enriched_context = self.object.get_website_data(context)
        if self.request.GET.get('subview') == 'minimal':
            self.template_name = "theme/institution_detail_popover.html"

        return enriched_context


def network_viz(request):
    return render(request, "theme/network.html")
