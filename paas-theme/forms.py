from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset
from django import forms
from haystack.forms import FacetedSearchForm, SearchForm
from haystack.query import SQ, AutoQuery
from apis_core.helper_functions.DateParser import parse_date


class PersonFacetedSearchForm(FacetedSearchForm):
    start_date_form = forms.CharField(required=False)
    end_date_form = forms.CharField(required=False)
    academy_member = forms.BooleanField(required=False)

    def search(self):
        super().search()
        if self.cleaned_data["q"] == "":
            sqs = self.searchqueryset.load_all()
        else:
            # sqs = super(PersonFacetedSearchForm, self).search()
            q = self.cleaned_data["q"]
            sqs = self.searchqueryset.filter(
                SQ(content=AutoQuery(q))
                | SQ(name=AutoQuery(q))
                | SQ(place_of_birth=AutoQuery(q))
                | SQ(place_of_death=AutoQuery(q))
            )
        if "academy_member" in self.cleaned_data.keys():
            wm = self.cleaned_data["academy_member"]
        else:
            wm = True
        if wm:
            sqs = sqs.filter(academy_member=True)
        # self.cleaned_data["academy_member"] = wm
        if len(self.selected_facets) == 0 and "selected_facets" in self.data.keys():
            if len(self.data["selected_facets"]) > 0:
                self.selected_facets = self.data["selected_facets"]
                if isinstance(self.selected_facets, str):
                    self.selected_facets = [self.selected_facets]
        for facet in self.selected_facets:
            if ":" not in facet:
                continue
            field, value = facet.split(":", 1)
            if value:
                sqs = sqs.narrow('%s:"%s"' % (field, sqs.query.clean(value)))
        if not self.is_valid():
            return self.no_query_found()
        if self.cleaned_data["start_date_form"]:
            sqs = sqs.filter(
                death_date__gte=parse_date(self.cleaned_data["start_date_form"])[0]
            )
        if self.cleaned_data["end_date_form"]:
            sqs = sqs.filter(
                birth_date__lte=parse_date(self.cleaned_data["end_date_form"])[0]
            )
        return sqs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PersonFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.helper.form_tag = False
        self.add_input(Submit("Filter", "Search"))
        self.layout = Layout(
            Fieldset("", "id", "name", "first_name", css_id="basic_search_fields"),
            Accordion(
                AccordionGroup(
                    "Lebensdaten", "start_date", "end_date", css_id="lebensdaten"
                ),
                AccordionGroup(
                    "Geburts- und Sterbeort",
                    "place_of_birth",
                    "place_of_death",
                    css_id="geburtsort",
                ),
                AccordionGroup(
                    "Beruf und Geschlecht", "profession", "gender", css_id="more"
                ),
                AccordionGroup(
                    "Anmerkungen", "notes", "collection", css_id="inventare"
                ),
            ),
        )
