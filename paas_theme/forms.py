from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset
from django import forms
from haystack.forms import FacetedSearchForm, SearchForm
from haystack.query import SQ, AutoQuery, SearchQuerySet
from apis_core.helper_functions.DateParser import parse_date
from apis_core.apis_entities.fields import Select2Multiple, ListSelect2


class PersonFilterFormHelperNew(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonFilterFormHelperNew, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.helper.form_tag = False
        self.add_input(Submit("Filter", "Search"))
        self.layout = Layout(
            Fieldset("", "q", css_id="basic_search_fields"),
            Accordion(
                AccordionGroup(
                    "Personendaten",
                    "name",
                    "gender",
                    "birth_date",
                    "death_date",
                    css_id="lebensdaten",
                ),
                AccordionGroup(
                    "Mitgliedschaft",
                    "mtgld_mitgliedschaft",
                    "mtgld_klasse",
                    css_id="mitgliedschaft",
                ),
                AccordionGroup(
                    "Akademischer CV",
                    "place_of_birth",
                    "place_of_death",
                    "profession",
                    css_id="akademischer_CV",
                ),
                AccordionGroup(
                    "In der Akademie",
                    "akademiemitgliedschaft",
                    "akademiefunktionen",
                    css_id="in_der_akademie",
                ),
                AccordionGroup(
                    "zur Wahl zum Akademiemitglied vorgeschlagen von",
                    "wahl_person",
                    "wahl_beruf",
                    "wahl_gender",
                    css_id="wahlvorschlag",
                ),
                AccordionGroup("Auszeichnungen", "nobelpreis", "ewk"),
            ),
        )


class PersonFacetedSearchFormNew(FacetedSearchForm):
    q = forms.CharField(required=False, label="Suche")
    start_date_form = forms.CharField(required=False)
    end_date_form = forms.CharField(required=False)
    death_date = forms.DateField(required=False)
    birth_date = forms.DateField(required=False)
    name = forms.CharField(required=False)
    akademiemitgliedschaft = forms.CharField(required=False)
    akademiefunktionen = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("funk_praesidentin", "Präsident/in"),
            ("funk_vizepraesidentin", "Vizepräsident/in"),
            ("funk_generalsekretaerin", "Generalsekretär"),
            ("funk_sekretaerin", "Sekretär "),
            ("funk_obfrau", "Obmann/Obfrau einer Kommission"),
            ("funk_mitgl_kommission", "Mitglied einer Kommission"),
            (
                "funk_obfrau_kurat",
                "Obmann/Obfrau eines Kuratoriums/Board eines Institut/einer Forschungsstelle",
            ),
            (
                "funk_direkt_forsch_inst",
                "Direktor/in eines Instituts/einer Forschungsstelle",
            ),
        ],
    )
    gender = forms.ChoiceField(
        required=False,
        choices=(("", "-"), ("male", "Männlich"), ("female", "Weiblich")),
        label="Geschlecht",
    )
    wahl_gender = forms.ChoiceField(
        required=False,
        choices=(("", "-"), ("male", "Männlich"), ("female", "Weiblich")),
        label="Geschlecht",
    )
    wahl_beruf = forms.CharField(required=False, label="Beruf")
    wahl_person = forms.CharField(required=False, label="Name")
    place_of_birth = forms.CharField(required=False, label="Geburtsort")
    place_of_death = forms.CharField(required=False, label="Sterbeort")
    profession = forms.CharField(required=False, label="Beruf")
    nobelpreis = forms.BooleanField(required=False, label="Nobelpreis")
    mtgld_mitgliedschaft = forms.MultipleChoiceField(
        required=False,
        label="Mitgliedschaft",
        choices=[
            ("", "-"),
            ("k. M. I.", "korrespondierendes Mitglied im Inland"),
            ("k. M. A.", "korrespondierendes Mitglied im Ausland"),
            ("w. M", "Wirkliches Mitglied"),
        ],
    )
    mtgld_klasse = forms.MultipleChoiceField(
        required=False,
        label="Klasse",
        choices=[
            ("", "-"),
            (
                "MATHEMATISCH-NATURWISSENSCHAFTLICHE",
                "Mathematisch-Naturwissenschaftliche Klasse",
            ),
            ("PHILOSOPHISCH-HISTORISCHE", "Philosophisch-Historische Klasse"),
        ],
    )
    ewk = forms.BooleanField(
        required=False, label="Österreichisches Ehrenzeichen für Wissenschaft und Kunst"
    )

    def search(self):
        super().search()
        if self.cleaned_data["q"] == "":
            sqs = self.searchqueryset.load_all()
        else:
            sqs = self.searchqueryset.filter(
                django_ct="apis_entities.person", academy_member=True
            ).filter(content=AutoQuery(self.cleaned_data["q"]))
        if self.cleaned_data["akademiefunktionen"]:
            funk_dict = SQ()
            for funk in self.cleaned_data["akademiefunktionen"]:
                funk_dict.add(SQ(**{funk: True}), SQ.OR)
            sqs = sqs.filter(funk_dict)
        if self.cleaned_data["gender"]:
            sqs = sqs.filter(gender=AutoQuery(self.cleaned_data["gender"]))
        if self.cleaned_data["name"]:
            sqs = sqs.filter(name=AutoQuery(self.cleaned_data["name"]))
        if self.cleaned_data["profession"]:
            sqs = sqs.filter(profession=AutoQuery(self.cleaned_data["profession"]))
        if (
            self.cleaned_data["mtgld_mitgliedschaft"]
            or self.cleaned_data["mtgld_klasse"]
        ):
            mtgld_dic = SQ()
            for mitgliedschaft in self.cleaned_data["mtgld_mitgliedschaft"]:
                mtgld_dic.add(SQ(akademiemitgliedschaft=mitgliedschaft), SQ.OR)
            kls_dict = SQ()
            for klasse in self.cleaned_data["mtgld_klasse"]:
                kls_dict.add(SQ(akademiemitgliedschaft=klasse), SQ.OR)
            sqs = sqs.filter(mtgld_dic & kls_dict)
        if (
            self.cleaned_data["wahl_beruf"]
            or self.cleaned_data["wahl_person"]
            or self.cleaned_data["wahl_gender"]
        ):
            dict_wahl = {"django_ct": "apis_relations.personperson"}
            if self.cleaned_data["wahl_beruf"]:
                dict_wahl["elected_by_profession"] = AutoQuery(
                    self.cleaned_data["wahl_beruf"]
                )
            if self.cleaned_data["wahl_person"]:
                dict_wahl["elected_by"] = AutoQuery(self.cleaned_data["wahl_person"])
            if self.cleaned_data["wahl_gender"]:
                dict_wahl["elected_by_gender"] = AutoQuery(
                    self.cleaned_data["wahl_gender"]
                )
            sqs2 = SearchQuerySet().filter(**dict_wahl)
            pers_ids = []
            for pers2 in sqs2:
                if pers2.elected_by_id not in pers_ids:
                    pers_ids.append(pers2.elected_by_id)
            sqs = sqs.filter(django_id__in=pers_ids)
        if self.cleaned_data["ewk"]:
            sqs = sqs.filter(ewk=self.cleaned_data["ewk"])
        if self.cleaned_data["nobelpreis"]:
            sqs = sqs.filter(nobelpreis=self.cleaned_data["nobelpreis"])
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
        self.helper = PersonFilterFormHelperNew()


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
