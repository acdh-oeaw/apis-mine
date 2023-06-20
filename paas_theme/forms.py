from apis_core.apis_vocabularies.models import (
    PersonInstitutionRelation,
    InstitutionType,
)
from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, Div, HTML, Hidden
from dal import autocomplete
from django import forms
from django.db.models.base import ModelBase
from django.forms.fields import MultipleChoiceField
from django.utils.translation import activate
from haystack.forms import FacetedSearchForm, SearchForm
from haystack.query import SQ, AutoQuery, SearchQuerySet
from haystack.inputs import Raw, Exact
from apis_core.helper_functions.DateParser import parse_date
from apis_core.apis_entities.fields import Select2Multiple, ListSelect2
from apis_core.apis_relations.models import PersonInstitution
from django.db.models import Q


from paas_theme.models import PAASMembership
from .provide_data import classes, get_child_classes


def get_map_haystack_form(form):
    array = [MultipleChoiceField, MultiSolrChildsField, MultiSolrField]
    res = []
    for field, class_name in form.fields.items():
        if class_name.__class__ in array:
            res.append(field)
    return res


class MultiSolrField(forms.MultipleChoiceField):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        return [(int(x.split("|")[0]), x.split("|")[1]) for x in value]

    def validate(self, value):
        """Check if value consists only of valid emails."""
        # Use the parent's handling of required fields, etc.
        if value:
            for x in value:
                if not isinstance(x, int):
                    return False
            return True
        elif value is None:
            return True
        return False


class MultiSolrChildsField(MultiSolrField):
    """Form field that extends the results to the child elements"""

    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        ids, lables = get_child_classes(
            [x.split("|")[0] for x in value], self._model_class, labels=True
        )
        value = [(int(x.split("|")[0]), x.split("|")[1]) for x in value]
        for idx, v in enumerate(ids):
            value.append((v, lables[idx]))
        return value

    def __init__(self, *args, model_class: ModelBase, **kwargs) -> None:
        super().__init__(**kwargs)
        self._model_class = model_class


class PersonFilterFormHelperNew(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonFilterFormHelperNew, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.helper.form_tag = False
        # self.template = "forms/template_person_form.html"
        self.add_input(
            Submit(
                "",
                "Kombinierte Auswertung starten",
                css_class="rounded-0 mt-3 text-uppercase w-100 text-left",
            )
        )
        self.layout = Layout(
            Fieldset("", "q", css_class="bg-mine", css_id="basic_search_fields"),
            Div(
                Div(
                    Accordion(
                        Hidden("start_date_form", ""),
                        Hidden("end_date_form", ""),
                        Hidden("start_date_form_exclusive", ""),
                        Hidden("end_date_form_exclusive", ""),
                        Hidden("start_date_life_form", ""),
                        Hidden("end_date_life_form", ""),
                        Div(
                            Fieldset(
                                "",
                                "mtgld_mitgliedschaft",
                                "mtgld_klasse",
                                css_id="mitgliedschaft",
                                css_class="show card-body card filter-wrapper pb-1",
                            ),
                            HTML(  # Mitgliedschaft slider
                                """ <div class="px-3 pb-3 pt-1">
                                        <label id="mitgleidschaft-slider-label" class="font-weight-bold pb-5">Mitgliedschaft im Zeitraum</label>
                                            <div class="slider-container pt-3">
                                                <div data-start-form="start_date_form" data-end-form="end_date_form" class="range-slider" data-range-start="{{form_membership_start_date}}" data-range-end="{{form_membership_end_date}}">
                                            </div>
                                            <div class="mt-3 d-flex align-items-center">
                                        <input class="form-control form-control-sm w-25 mr-2" type="text" id="start_date_input" value="{{form_membership_start_date}}"/><input type="checkbox" class="mt-1 ml-1" id="start_date_exclusive_checkbox"/><span class="ml-1">⟼</span>
                                        
                                        <div class="w-50"></div><span class="mr-1">⟻</span><input type="checkbox" class="mt-1 mr-2"  id="end_date_exclusive_checkbox" class="mr-2"/>
                                        <input class="form-control form-control-sm w-25" type="text" id="end_date_input" value="{{form_membership_end_date}}"/>
                  </div>
                                        </div>
                                    </div>"""
                            ),
                            css_class="bg-white",
                        ),
                    ),
                    css_class="col-md-6 pt-30 pr-0 pr-md-custom pl-0 align-items-md-stretch d-flex",
                ),
                Div(
                    Accordion(
                        AccordionGroup(
                            "Funktionen im Präsidium",
                            "pres_funktionen",
                            css_id="praesidium",
                        ),
                        AccordionGroup(
                            "Geschlecht",
                            "gender",
                            css_id="geschlecht",
                        ),
                        AccordionGroup(
                            "Lebenslauf",
                            HTML(  # DEBUG: TURNED OFF RANGE SLIDER
                                """<div class="pb-3 pt-1">
                                        <label class="pb-5">Leben im Zeitraum</label>
                                        <div class="slider-container pt-3">
                                            <div data-start-form="start_date_life_form" data-end-form="end_date_life_form" class="range-sliderOFF">
                                            </div>
                                        </div>
                                    </div>"""
                            ),
                            "place_of_birth",
                            "place_of_death",
                            "schule",
                            "uni",
                            "uni_habil",
                            "fach_habilitation",
                            "profession",
                            Fieldset(
                                "Berufliche Positionen",
                                "beruf_position",
                                "beruf_institution",
                                css_id="beruf_subform",
                            ),
                            "mgld_nsdap",
                            css_id="akademischer_CV",
                        ),
                        AccordionGroup(
                            "Funktionen in Akademieinstitutionen",
                            "akademiefunktionen",
                            css_id="in_der_akademie",
                        ),
                        AccordionGroup(
                            "zur Wahl vorgeschlagen von",
                            "wahl_person",
                            "wahl_beruf",
                            "wahl_gender",
                            css_id="wahlvorschlag",
                        ),
                        AccordionGroup(
                            "Wissenschaftler/innen/austausch", "wiss_austausch"
                        ),
                        AccordionGroup("Auszeichnungen", "nobelpreis", "ewk"),
                    ),
                    css_class="col-md-6 pt-30 pr-0 pl-0 pl-md-custom",
                ),
                css_class="row ml-0 mr-0 mt-4",
            ),
        )


class PersonFacetedSearchFormNew(FacetedSearchForm):
    q = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Mitgliedersuche",
                "class": "border-0 rounded-0 d-block mx-auto w-75",
            }
        ),
        required=False,
        label="",
    )
    start_date_form = forms.CharField(required=False)
    end_date_form = forms.CharField(required=False)
    start_date_form_exclusive = forms.BooleanField(
        required=False, label="Membership start not before"
    )
    end_date_form_exclusive = forms.BooleanField(required=False)
    start_date_life_form = forms.CharField(required=False)
    end_date_life_form = forms.CharField(required=False)
    start_date_life_form_exclusive = forms.CharField(required=False)
    end_date_life_form_exclusive = forms.CharField(required=False)
    death_date = forms.DateField(required=False)
    birth_date = forms.DateField(required=False)
    name = forms.CharField(required=False)
    akademiemitgliedschaft = forms.CharField(required=False)
    akademiefunktionen = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={"class": "select2-main"}),
        label="",
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
    pres_funktionen = forms.MultipleChoiceField(
        required=False,
        label="",
        widget=forms.CheckboxSelectMultiple(),
        choices=[
            ("funk_praesidentin", "Präsident/in"),
            ("funk_vizepraesidentin", "Vizepräsident/in"),
            ("funk_generalsekretaerin", "Generalsekretär/in"),
            ("funk_sekretaerin", "Sekretär/in"),
            ("funk_klassenpres_math_nat", "Klassenpräsident/in math.-nat. Klasse"),
            ("funk_klassenpres_phil_hist", "Klassenpräsident/in phil.-hist. Klasse"),
        ],
    )
    gender = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "select2-main no-search rounded-0"}),
        required=False,
        choices=(
            ("", "-"),
            ("männlich", "Männlich"),
            ("weiblich", "Weiblich"),
            ("unbekannt", "Unbekannt"),
        ),
        label="",
    )
    wahl_gender = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "select2-main no-search rounded-0"}),
        required=False,
        choices=(("", "-"), ("male", "Männlich"), ("female", "Weiblich")),
        label="Geschlecht",
    )
    wahl_beruf = forms.CharField(required=False, label="Beruf")
    wahl_person = forms.CharField(required=False, label="Name")
    place_of_birth = MultiSolrField(
        required=False,
        label="Geburtsort",
        widget=Select2Multiple(
            url="paas_theme:paas_place_of_birth_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    place_of_death = MultiSolrField(
        required=False,
        label="Sterbeort",
        widget=Select2Multiple(
            url="paas_theme:paas_place_of_death_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    profession = MultiSolrField(
        required=False,
        label="Beruf",
        widget=Select2Multiple(
            url="paas_theme:paas_person_beruf_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    nobelpreis = forms.BooleanField(required=False, label="Nobelpreis")
    beruf_position = MultiSolrChildsField(
        model_class=PersonInstitutionRelation,
        required=False,
        label="Position",
        widget=Select2Multiple(
            url="paas_theme:paas_position_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    beruf_institution = MultiSolrField(
        required=False,
        label="Institution",
        widget=Select2Multiple(
            url="paas_theme:paas_institution_autocomplete",
            forward=["beruf_position"],
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    mgld_nsdap = forms.BooleanField(required=False, label="Mitglied der NSDAP")
    mtgld_mitgliedschaft = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Mitgliedschaft",
        choices=[
            ("kM I", "korrespondierendes Mitglied im Inland"),
            ("kM A", "korrespondierendes Mitglied im Ausland"),
            ("wM", "Wirkliches Mitglied"),
            ("em", "Ehrenmitglied"),
            ("Junge Kurie/Junge Akademie", "Junge Kurie/Junge Akademie"),
        ],
    )
    mtgld_klasse = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Klasse",
        choices=[
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
    wiss_austausch = MultiSolrField(
        required=False,
        label="Land",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_place_wiss_austausch_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    schule = MultiSolrField(
        required=False,
        label="Schule",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_schule_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    uni = MultiSolrField(
        required=False,
        label="Universität",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_uni_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    uni_habil = MultiSolrField(
        required=False,
        label="Universität Habilitation",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_uni_habil_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    fach_habilitation = MultiSolrField(
        required=False,
        label="Habilitationsfach",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_habil_fach_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )

    def is_valid(self) -> bool:
        val = super().is_valid()
        return val

    def search(self):
        # print("PERSON FACETED SEARCH FORM NEW")
        super().search()

        pers_ids = []
        sqs = self.searchqueryset.filter(
            django_ct="paas_theme.paasperson", academy_member=True
        )
        if self.cleaned_data["q"] != "":
            sqs = sqs.filter(content=AutoQuery(self.cleaned_data["q"]))
        if self.cleaned_data["akademiefunktionen"]:
            funk_dict = SQ()
            for funk in self.cleaned_data["akademiefunktionen"]:
                funk_dict.add(SQ(**{funk: True}), SQ.OR)
            sqs = sqs.filter(funk_dict)
        for feld in [
            "gender",
        ]:
            if self.cleaned_data[feld]:
                f_dict_for = {feld: AutoQuery(self.cleaned_data[feld])}
                sqs = sqs.filter(**f_dict_for)
        for feld in [
            ("uni", "universitaet_id__in"),
            ("schule", "schule_id__in"),
            ("profession", "profession_id__in"),
            ("uni_habil", "uni_habilitation_id__in"),
            ("fach_habilitation", "fach_habilitation_id__in"),
            ("wiss_austausch", "w_austausch_id__in"),
            ("place_of_birth", "place_of_birth_id__in"),
            ("place_of_death", "place_of_death_id__in"),
        ]:
            if len(self.cleaned_data[feld[0]]) > 0:
                sqs = sqs.filter(
                    **{feld[1]: [str(x[0]) for x in self.cleaned_data[feld[0]]]}
                )
        if self.cleaned_data["mgld_nsdap"]:
            sqs = sqs.filter(mitglied_nsdap=self.cleaned_data["mgld_nsdap"])
        if self.cleaned_data["pres_funktionen"]:
            pres_funk_dict = SQ()
            for funk in self.cleaned_data["pres_funktionen"]:
                pres_funk_dict.add(SQ(**{funk: True}), SQ.OR)
            sqs = sqs.filter(pres_funk_dict)
        if (
            self.cleaned_data["mtgld_mitgliedschaft"]
            or self.cleaned_data["mtgld_klasse"]
        ) and not self.cleaned_data["start_date_form"]:
            mtgld_dic = SQ()
            for mitgliedschaft in self.cleaned_data["mtgld_mitgliedschaft"]:
                mtgld_dic.add(
                    SQ(akademiemitgliedschaft_exact=Exact(mitgliedschaft)), SQ.OR
                )
            kls_dict = SQ()
            for klasse in self.cleaned_data["mtgld_klasse"]:
                kls_dict.add(SQ(klasse_person=klasse), SQ.OR)
            sqs = sqs.filter(mtgld_dic & kls_dict)
        # TODO: This looks unnecessary requirement for self.cleaned_data["mtgld_mitgliedschaft"] or self.cleaned_data["mtgld_klasse"]
        elif self.cleaned_data["start_date_form"]:
            ids_person = PAASMembership.objects.get_memberships(
                start=self.cleaned_data["start_date_form"],
                end=self.cleaned_data["end_date_form"],
                institutions=self.cleaned_data.get("mtgld_klasse", None),
                memberships=self.cleaned_data.get("mtgld_mitgliedschaft", None),
                start_exclusive=self.cleaned_data.get("start_date_form_exclusive"),
                end_exclusive=self.cleaned_data.get("end_date_form_exclusive"),
            ).get_person_ids()
            sqs = sqs.filter(django_id__in=ids_person)
        if self.cleaned_data["ewk"]:
            sqs = sqs.filter(ewk=self.cleaned_data["ewk"])
        if self.cleaned_data["nobelpreis"]:
            sqs = sqs.filter(nobelpreis=self.cleaned_data["nobelpreis"])
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
            for pers2 in sqs2:
                if pers2.elected_by_id not in pers_ids:
                    pers_ids.append(pers2.elected_by_id)
        if (
            self.cleaned_data["beruf_position"]
            or self.cleaned_data["beruf_institution"]
        ):
            q_dict3 = {
                "django_ct": "apis_relations.personinstitution",
            }
            if len(self.cleaned_data["beruf_position"]) > 0:
                q_dict3["relation_type_id__in"] = self.cleaned_data["beruf_position"]
            if len(self.cleaned_data["beruf_institution"]) > 0:
                q_dict3["institution_id__in"] = self.cleaned_data["beruf_institution"]
            sqs3 = SearchQuerySet().filter(**q_dict3)
            for pers2 in sqs3:
                if pers2.person_id not in pers_ids:
                    pers_ids.append(pers2.person_id)
        if len(pers_ids) > 0:
            sqs = sqs.filter(django_id__in=pers_ids)

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
        if self.cleaned_data["start_date_life_form"]:
            sqs = sqs.filter(
                death_date__gte=parse_date(self.cleaned_data["start_date_life_form"])[0]
            )
            if self.cleaned_data.get("start_date_life_form_exclusive"):
                sqs = sqs.filter(
                    birth_date__gte=parse_date(
                        self.cleaned_data["start_date_life_form"]
                    )[0]
                )
        if self.cleaned_data["end_date_life_form"]:
            sqs = sqs.filter(
                birth_date__lte=parse_date(self.cleaned_data["end_date_life_form"])[0]
            )

            if self.cleaned_data.get("end_date_life_form_exclusive"):
                sqs = sqs.filter(
                    death_date__lte=parse_date(self.cleaned_data["end_date_life_form"])[
                        0
                    ]
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


class InstitutionFilterFormHelperNew(FormHelper):
    def __init__(self, *args, **kwargs):
        super(InstitutionFilterFormHelperNew, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.helper.form_tag = False
        # self.template = "forms/template_person_form.html"
        self.add_input(
            Submit(
                "",
                "Kombinierte Auswertung starten",
                css_class="rounded-0 mt-3 text-uppercase  w-100 text-left",
            )
        )
        self.layout = Layout(
            Fieldset("", "q", css_class="bg-mine", css_id="basic_search_fields"),
            Div(
                Div(
                    Accordion(
                        Hidden("start_date_form", ""),
                        Hidden("end_date_form", ""),
                        Hidden("start_date_form_exclusive", ""),
                        Hidden("end_date_form_exclusive", ""),
                        Fieldset(
                            "",
                            "institution_art",
                            "institution_klasse",
                            css_id="mitgliedschaft",
                            css_class="show card-body card filter-wrapper",
                        ),
                        HTML(  # Mitgliedschaft slider
                            """ <div class="px-3 pb-3 pt-1 mt-3">
                                        <label id="bestehen-slider-label" class="font-weight-bold pb-5">Bestehen im Zeitraum</label>
                                            <div class="slider-container pt-3">
                                                <div data-start-form="start_date_form" data-end-form="end_date_form" class="range-slider" data-range-start="{{form_institution_start_date}}" data-range-end="{{form_institution_end_date}}">
                                            </div>
                                            <div class="mt-3 d-flex align-items-center">
                                        <input class="form-control form-control-sm w-25 mr-2" type="text" id="start_date_input" value="{{form_institution_start_date}}"/><input type="checkbox" class="mt-1 ml-1" id="start_date_exclusive_checkbox"/><span class="ml-1">⟼</span>
                                        
                                        <div class="w-50"></div><span class="mr-1">⟻</span><input type="checkbox" class="mt-1 mr-2"  id="end_date_exclusive_checkbox" class="mr-2"/>
                                        <input class="form-control form-control-sm w-25" type="text" id="end_date_input" value="{{form_institution_end_date}}"/>
                  </div>
                                        </div>
                                    </div>"""
                        ),
                    ),
                    css_class="col-md-6 pt-30 pr-0 pr-md-custom pl-0",
                ),
                Div(
                    Accordion(
                        AccordionGroup(
                            "Akademiemitglieder in Akademieinstitutionen",
                            "akademiefunktionen",
                            css_id="in_der_akademie",
                        ),
                    ),
                    css_class="col-md-6 pt-30 pr-0 pl-0 pl-md-15",
                ),
                css_class="row ml-0 mr-0 mt-4",
            ),
        )


class InstitutionFacetedSearchFormNew(FacetedSearchForm):
    q = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Institutionensuche",
                "class": "border-0 rounded-0 d-block mx-auto w-75",
            }
        ),
        required=False,
        label="",
    )
    start_date_form = forms.CharField(required=False)
    end_date_form = forms.CharField(required=False)
    death_date = forms.DateField(required=False)
    birth_date = forms.DateField(required=False)
    name = forms.CharField(required=False)

    institution_art = forms.MultipleChoiceField(
        required=False,
        label="Art",
        widget=forms.CheckboxSelectMultiple(),
        choices=[
            (i.pk, i.name)
            for i in InstitutionType.objects.filter(parent_class_id=81).exclude(
                pk__in=[85, 4236]
            )
        ]
        + [(i.pk, i.name) for i in InstitutionType.objects.filter(pk=137)],
    )

    institution_klasse = forms.MultipleChoiceField(
        required=False,
        label="Klasse",
        widget=forms.CheckboxSelectMultiple(),
        choices=[
            (2, "Philosophisch-Historische Klasse"),
            (3, "Mathematisch-Naturwissenschaftliche Klasse"),
            (1, "Gesamtakademie"),
        ],
    )

    akademiemitgliedschaft = forms.CharField(required=False)
    akademiefunktionen = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={"class": "select2-main"}),
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
    pres_funktionen = forms.MultipleChoiceField(
        required=False,
        label="Funktionen",
        widget=forms.CheckboxSelectMultiple(),
        choices=[
            ("funk_praesidentin", "Präsident/in"),
            ("funk_vizepraesidentin", "Vizepräsident/in"),
            ("funk_generalsekretaerin", "Generalsekretär/in"),
            ("funk_sekretaerin", "Sekretär/in"),
            ("funk_klassenpres_math_nat", "Klassenpräsident/in math.-nat. Klasse"),
            ("funk_klassenpres_phil_hist", "Klassenpräsident/in phil.-hist. Klasse"),
        ],
    )
    gender = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "bootstrap-select rounded-0"}),
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
    place_of_birth = MultiSolrField(
        required=False,
        label="Geburtsort",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_place_of_birth_autocomplete",
        ),
    )
    place_of_death = MultiSolrField(
        required=False,
        label="Sterbesort",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_place_of_death_autocomplete",
        ),
    )
    profession = MultiSolrField(
        required=False,
        label="Beruf",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_person_beruf_autocomplete",
        ),
    )
    nobelpreis = forms.BooleanField(required=False, label="Nobelpreis")
    beruf_position = MultiSolrChildsField(
        model_class=PersonInstitutionRelation,
        required=False,
        label="Position",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_position_autocomplete",
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    beruf_institution = MultiSolrField(
        required=False,
        label="Institution",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_autocomplete",
            forward=["beruf_position"],
            attrs={"data-theme": "bootstrap4"},
        ),
    )
    mgld_nsdap = forms.BooleanField(required=False, label="Mitglied der NSDAP")
    mtgld_mitgliedschaft = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={"class": "select2-main"}),
        required=False,
        label="Mitgliedschaft",
        choices=[
            ("", "-"),
            ("kM I", "korrespondierendes Mitglied im Inland"),
            ("kM A", "korrespondierendes Mitglied im Ausland"),
            ("wM", "Wirkliches Mitglied"),
            ("em", "Ehrenmitglied"),
        ],
    )
    mtgld_klasse = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={"class": "select2-main"}),
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
    wiss_austausch = MultiSolrField(
        required=False,
        label="Land",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_place_wiss_austausch_autocomplete",
        ),
    )
    schule = MultiSolrField(
        required=False,
        label="Schule",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_schule_autocomplete",
        ),
    )
    uni = MultiSolrField(
        required=False,
        label="Universität",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_uni_autocomplete",
        ),
    )
    uni_habil = MultiSolrField(
        required=False,
        label="Universität Habilitation",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_uni_habil_autocomplete",
        ),
    )
    fach_habilitation = MultiSolrField(
        required=False,
        label="Habilitationsfach",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_habil_fach_autocomplete",
        ),
    )

    def is_valid(self) -> bool:
        val = super().is_valid()
        return val

    def search(self):
        super().search()
        sqs = self.searchqueryset.filter(
            django_ct="apis_entities.institution",
        )
        if "institution_art" in self.data.keys():
            sqs = sqs.filter(institution_art=self.data["institution_art"])
        if "institution_klasse" in self.data.keys():
            sqs = sqs.filter(institution_klasse=self.data["institution_klasse"])
        if "related_institution" in self.data.keys():
            kwargs = {"load_all": True, "searchqueryset": SearchQuerySet()}
            map_haystack_form_fields = get_map_haystack_form(
                PersonFacetedSearchFormNew()
            )
            q_dict_inter = dict()
            for k, v in self.data.items():
                if k.startswith("p_"):
                    if k[2:] in map_haystack_form_fields:
                        v = [v]
                    q_dict_inter[k[2:]] = v
            p_objects = PersonFacetedSearchFormNew(q_dict_inter, **kwargs).search()
            qs_persinst = []
            if isinstance(self.data["related_institution"], str):
                rel_config = [self.data["related_institution"]]
            else:
                rel_config = self.data["related_institution"]
            for relation_type in rel_config:
                qs_persinst_2 = classes["linked_search_institution"][relation_type][
                    "qs"
                ]
                qs_persinst_2["related_person_id__in"] = list(
                    p_objects.values_list("pk", flat=True)
                )
                qs_persinst.append(Q(**qs_persinst_2))
            if len(qs_persinst) > 1:
                p_objects_2 = PersonInstitution.objects.filter(
                    Q(qs_persinst, _connector=Q.OR)
                )
            else:
                p_objects_2 = PersonInstitution.objects.filter(qs_persinst[0])
            sqs = sqs.filter(
                django_id__in=list(
                    set(p_objects_2.values_list("related_institution_id", flat=True))
                )
            )
        if self.cleaned_data["q"] != "":
            sqs = sqs.filter(content=AutoQuery(self.cleaned_data["q"]))
        if self.cleaned_data["akademiefunktionen"]:
            funk_dict = SQ()
            for funk in self.cleaned_data["akademiefunktionen"]:
                funk_dict.add(SQ(**{funk: True}), SQ.OR)
            sqs = sqs.filter(funk_dict)
        for feld in [
            "gender",
        ]:
            if self.cleaned_data[feld]:
                f_dict_for = {feld: AutoQuery(self.cleaned_data[feld])}
                sqs = sqs.filter(**f_dict_for)
        for feld in [
            ("uni", "universitaet_id__in"),
            ("schule", "schule_id__in"),
            ("profession", "profession_id__in"),
            ("uni_habil", "uni_habilitation_id__in"),
            ("fach_habilitation", "fach_habilitation_id__in"),
            ("wiss_austausch", "w_austausch_id__in"),
            ("place_of_birth", "place_of_birth_id__in"),
            ("place_of_death", "place_of_death_id__in"),
        ]:
            if len(self.cleaned_data[feld[0]]) > 0:
                sqs = sqs.filter(
                    **{feld[1]: [str(x) for x in self.cleaned_data[feld[0]]]}
                )
        if self.cleaned_data["mgld_nsdap"]:
            sqs = sqs.filter(mitglied_nsdap=self.cleaned_data["mgld_nsdap"])
        if self.cleaned_data["pres_funktionen"]:
            pres_funk_dict = SQ()
            for funk in self.cleaned_data["pres_funktionen"]:
                pres_funk_dict.add(SQ(**{funk: True}), SQ.OR)
            sqs = sqs.filter(pres_funk_dict)
        if (
            self.cleaned_data["mtgld_mitgliedschaft"]
            or self.cleaned_data["mtgld_klasse"]
        ):
            mtgld_dic = SQ()
            for mitgliedschaft in self.cleaned_data["mtgld_mitgliedschaft"]:
                mtgld_dic.add(SQ(akademiemitgliedschaft=mitgliedschaft), SQ.OR)
            kls_dict = SQ()
            for klasse in self.cleaned_data["mtgld_klasse"]:
                kls_dict.add(SQ(klasse_person=klasse), SQ.OR)
            sqs = sqs.filter(mtgld_dic & kls_dict)
        if self.cleaned_data["ewk"]:
            sqs = sqs.filter(ewk=self.cleaned_data["ewk"])
        if self.cleaned_data["nobelpreis"]:
            sqs = sqs.filter(nobelpreis=self.cleaned_data["nobelpreis"])
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
        if (
            self.cleaned_data["beruf_position"]
            or self.cleaned_data["beruf_institution"]
        ):
            q_dict3 = {
                "django_ct": "apis_relations.personinstitution",
            }
            if len(self.cleaned_data["beruf_position"]) > 0:
                q_dict3["relation_type_id__in"] = self.cleaned_data["beruf_position"]
            if len(self.cleaned_data["beruf_institution"]) > 0:
                q_dict3["institution_id__in"] = self.cleaned_data["beruf_institution"]
            sqs3 = SearchQuerySet().filter(**q_dict3)
            pers_ids = []
            for pers2 in sqs3:
                if pers2.person_id not in pers_ids:
                    pers_ids.append(pers2.person_id)
            sqs = sqs.filter(django_id__in=pers_ids)

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
                end_date__gte=parse_date(self.cleaned_data["start_date_form"])[0]
            )
            if self.cleaned_data.get("start_date_form_exclusive"):
                sqs = sqs.filter(
                    start_date__gte=parse_date(self.cleaned_data["start_date_form"])[0]
                )

        if self.cleaned_data["end_date_form"]:
            sqs = sqs.filter(
                start_date__lte=parse_date(self.cleaned_data["end_date_form"])[0]
            )

            if self.cleaned_data.get("end_date_form_exclusive"):
                sqs = sqs.filter(
                    end_date__lte=parse_date(self.cleaned_data["end_date_form"])[0]
                )
        return sqs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = InstitutionFilterFormHelperNew()


class InstitutionFacetedSearchForm(FacetedSearchForm):
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
