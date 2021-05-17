from apis_core.apis_vocabularies.models import PersonInstitutionRelation
from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, Div
from dal import autocomplete
from django import forms
from django.db.models.base import ModelBase
from django.forms.fields import MultipleChoiceField
from haystack.forms import FacetedSearchForm, SearchForm
from haystack.query import SQ, AutoQuery, SearchQuerySet
from haystack.inputs import Raw
from apis_core.helper_functions.DateParser import parse_date
from apis_core.apis_entities.fields import Select2Multiple, ListSelect2
from .provide_data import classes, get_child_classes


class MultiSolrField(forms.MultipleChoiceField):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        return [int(x) for x in value]

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
        return [int(x) for x in get_child_classes(value, self._model_class) + value]

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
        self.add_input(Submit("Filter", "Suche", css_class="rounded-0 mt-1"))
        self.layout = Layout(
            Fieldset("", "q", css_class="bg-mine", css_id="basic_search_fields"),
            Div(
                Div(
                    Accordion(
                        AccordionGroup(
                            "Mitgliedschaft",
                            "mtgld_mitgliedschaft",
                            "mtgld_klasse",
                            css_id="mitgliedschaft",
                        ),
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
                                css_class="form-inline",
                            ),
                            "mgld_nsdap",
                            css_id="akademischer_CV",
                        ),
                    ),
                    css_class="col-md-6 pt-30 pr-0 pr-md-15 pl-0",
                ),
                Div(
                    Accordion(
                        AccordionGroup(
                            "Funktionen in der Akademie",
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
                    css_class="col-md-6 pt-30 pr-0 pl-0 pl-md-15",
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
    death_date = forms.DateField(required=False)
    birth_date = forms.DateField(required=False)
    name = forms.CharField(required=False)
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
        ),
    )
    beruf_institution = MultiSolrField(
        required=False,
        label="Institution",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_autocomplete", forward=["beruf_position"]
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
            django_ct="apis_entities.person", academy_member=True
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

class InstitutionFilterFormHelperNew(FormHelper):
    def __init__(self, *args, **kwargs):
        super(InstitutionFilterFormHelperNew, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.helper.form_tag = False
        # self.template = "forms/template_person_form.html"
        self.add_input(Submit("Filter", "Suche", css_class="rounded-0 mt-1"))
        self.layout = Layout(
            Fieldset("", "q", css_class="bg-mine", css_id="basic_search_fields"),
            Div(
                Div(
                    Accordion(
                        AccordionGroup(
                            "Akademieinstitutionen",
                            "mtgld_mitgliedschaft",
                            "mtgld_klasse",
                            css_id="akademieinstitutionen",
                        ),
                    ),
                    css_class="col-md-6 pt-30 pr-0 pr-md-15 pl-0",
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
        ),
    )
    beruf_institution = MultiSolrField(
        required=False,
        label="Institution",
        widget=autocomplete.Select2Multiple(
            url="paas_theme:paas_institution_autocomplete", forward=["beruf_position"]
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
            django_ct="apis_entities.institution"
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
                death_date__gte=parse_date(self.cleaned_data["start_date_form"])[0]
            )
        if self.cleaned_data["end_date_form"]:
            sqs = sqs.filter(
                birth_date__lte=parse_date(self.cleaned_data["end_date_form"])[0]
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