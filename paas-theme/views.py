import random

import requests
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

from apis_core.apis_entities.models import Person
from browsing.browsing_utils import GenericListView
from webpage.views import get_imprint_url
from .filters import PersonListFilter
from .forms import PersonFilterFormHelper, PersonFacetedSearchForm
from .tables import PersonTable, SearchResultTable
from .utils import (
    oebl_persons,
    get_daily_entries,
    get_featured_person,
    enrich_person_context,
)
from haystack.generic_views import FacetedSearchView
from haystack.forms import FacetedSearchForm
from haystack.query import SearchQuerySet
from haystack.query import RelatedSearchQuerySet
from haystack.models import SearchResult
from django.shortcuts import render_to_response

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from django_tables2.config import RequestConfig


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
        context["featured_pers"] = get_featured_person()
        enriched_context = get_daily_entries(context, oebl_persons)
        enriched_context["random_entries"] = random.sample(list(oebl_persons), 2)
        return enriched_context


class AboutView(TemplateView):
    template_name = "theme/about.html"


class ContactView(TemplateView):
    template_name = "theme/contact.html"


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


class PersonSearchView(FacetedSearchView):
    queryset = SearchQuerySet()
    form_class = PersonFacetedSearchForm
    facet_fields = [
        "place_of_birth",
        "place_of_death",
        "comissions",
        "profession",
        "education",
        "career",
    ]


class SearchView(SingleTableMixin, PersonSearchView):
    table_class = SearchResultTable
    template_name = "theme/person_search.html"

    def get_table_data(self):
        return self.queryset


class PersonDetailView(DetailView):
    model = Person
    template_name = "theme/person_detail.html"

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

        return enriched_context


def network_viz(request):
    return render_to_response('theme/network.html')
