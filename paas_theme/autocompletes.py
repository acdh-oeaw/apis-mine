from dal import autocomplete
from haystack.query import SQ, AutoQuery, SearchQuerySet
from django.utils.html import format_html
from .provide_data import classes


def get_date_label(item):
    date = False
    if item.start_date or item.end_date:
        if item.start_date:
            sd = item.start_date.strftime("%Y")
        else:
            sd = "ka"
        if item.end_date:
            ed = item.end_date.strftime("%Y")
        else:
            ed = "ka"
        date = f"({sd} - {ed})"
    return date


class PaasPersonAutocomplete(autocomplete.Select2QuerySetView):
    f = {"django_ct": "paas_theme.paasperson"}

    def get_result_value(self, result):
        return f"{result.pk}|{result.name}"

    def get_result_label(self, item):
        lbl = item.name
        date = get_date_label(item)
        if date:
            lbl += f" {date}"
        return lbl

    def get_queryset(self):
        query_object = SQ(**self.f)
        if self.q:
            query_object &= SQ(name=self.q)

        return SearchQuerySet().filter(query_object)


class PaasInstitutionAutocomplete(autocomplete.Select2QuerySetView):
    f = {"django_ct": "apis_entities.institution", "academy": False}

    def get_result_value(self, result):
        return f"{result.pk}|{result.name}"

    def get_result_label(self, item):
        lbl = item.name
        date = get_date_label(item)
        if date:
            lbl += f" {date}"
        return lbl

    def get_queryset(self):
        # sqs = SearchQuerySet().filter(django_ct="apis_entities.institution")
        if self.q:
            self.f["name_auto"] = self.q
        if "beruf_position" in self.forwarded.keys():
            position_dict = SQ()
            if isinstance(self.forwarded["beruf_position"], str):
                self.forwarded["beruf_position"] = [self.forwarded["beruf_position"]]
            for pos in self.forwarded["beruf_position"]:
                position_dict.add(SQ(relation_types_person_id=pos), SQ.OR)
            sqs = SearchQuerySet().filter(SQ(**self.f) & position_dict)
        else:
            sqs = SearchQuerySet().filter(**self.f)
        return sqs


class PaasPersonInstitutionRelationAutocomplete(autocomplete.Select2QuerySetView):
    f = {"django_ct": "apis_vocabularies.personinstitutionrelation"}
    kind = None

    def get_result_value(self, result):
        return f"{result.pk}|{result.name}"

    def get_result_label(self, item):
        lbl = item.text
        return lbl

    def get_queryset(self):
        # sqs = SearchQuerySet().filter(django_ct="apis_entities.institution")
        if self.q:
            self.f["label_auto"] = self.q
        if self.kind is not None:
            self.f["kind"] = self.kind
        sqs = SearchQuerySet().filter(**self.f)
        return sqs


class PaasHabilitationFachAutocomplete(PaasPersonInstitutionRelationAutocomplete):
    kind = "Habilitation"

    def get_result_label(self, item):
        return item.text.split(">>")[-1].strip()


class PaasPersonInstitutionPositionAutocomplete(
    PaasPersonInstitutionRelationAutocomplete
):
    kind = "Beruf"


class PaasInstitutionUniAutocomplete(PaasInstitutionAutocomplete):
    f = {
        "django_ct": "apis_entities.institution",
        "relation_types_person_id__in": [1369, 1371],
    }


class PaasInstitutionSchuleAutocomplete(PaasInstitutionAutocomplete):
    f = {
        "django_ct": "apis_entities.institution",
        "relation_types_person_id__in": [176],
    }


class PaasInstitutionUniHabilitationAutocomplete(PaasInstitutionAutocomplete):
    f = {
        "django_ct": "apis_entities.institution",
        "relation_types_person_id__in": classes["habilitation"],
    }


class PaasPlaceAutocomplete(autocomplete.Select2QuerySetView):
    f = {"django_ct": "apis_entities.place"}

    def get_result_value(self, result):
        return f"{result.pk}|{result.name}"

    def get_result_label(self, item):
        lbl = item.name
        return lbl

    def get_queryset(self):
        # sqs = SearchQuerySet().filter(django_ct="apis_entities.institution")
        if self.q:
            self.f["name_auto"] = self.q
        sqs = SearchQuerySet().filter(**self.f)
        return sqs


class PaasProfessionAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete for the professions"""

    f = {"django_ct": "apis_vocabularies.professiontype"}

    def get_result_value(self, result):
        return f"{result.pk}|{result.name}"

    def get_result_label(self, item):
        lbl = item.text
        return lbl

    def get_queryset(self):
        # sqs = SearchQuerySet().filter(django_ct="apis_entities.institution")
        if self.q:
            self.f["label_auto"] = self.q
        sqs = SearchQuerySet().filter(**self.f)
        return sqs


class PaasPlaceBirthAutocomplete(PaasPlaceAutocomplete):
    """Autocomplet only returning places that have a birth event attached"""

    f = {
        "django_ct": "apis_entities.place",
        "relation_types_person_id__in": [64, 3090, 152],
    }


class PaasPlaceDeathAutocomplete(PaasPlaceAutocomplete):
    """Autocomplet only returning places that have a death event attached"""

    f = {
        "django_ct": "apis_entities.place",
        "relation_types_person_id__in": [153, 3054, 3091],
    }


class PaasPlaceWAustauschAutocomplete(PaasPlaceAutocomplete):
    """Autocomplete returning Places that have a Wissenschaftler Austausch attached"""

    f = {"django_ct": "apis_entities.place", "relation_types_person_id": 3375}
