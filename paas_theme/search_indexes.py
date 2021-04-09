from haystack import indexes
from django.conf import settings

from apis_core.apis_metainfo.models import Text
from apis_core.apis_vocabularies.models import LabelType
from apis_core.apis_labels.models import Label
from .utils import oebl_persons
from apis_core.apis_entities.models import Person, Institution, Place
from apis_core.apis_relations.models import PersonInstitution, PersonPerson
from .serializer import (
    get_child_classes,
    get_child_institutions_from_parent,
    get_mitgliedschaft_from_relation,
    abbreviate,
    subs_akademie,
)
from .utils import classes


class InstitutionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    start_date = indexes.DateField(model_attr="start_date", null=True)
    end_date = indexes.DateField(model_attr="end_date", null=True)
    # located_in = indexes.CharField(null=True)
    # located_in_id = indexes.IntegerField(null=True)
    # located_at = indexes.LocationField(null=True)

    def get_model(self):
        return Institution


class FunktionenAkademieIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    person = indexes.CharField(model_attr="related_person")
    person_id = indexes.IntegerField(model_attr="related_person_id")
    start_date = indexes.DateField(model_attr="start_date", null=True)
    end_date = indexes.DateField(model_attr="end_date", null=True)
    institution_id = indexes.IntegerField(model_attr="related_institution_id")
    institution = indexes.CharField(model_attr="related_institution")
    institution_type = indexes.CharField(model_attr="related_institution__kind__name")

    def get_model(self):
        return PersonInstitution

    def index_queryset(self, using=None):
        self.get_model().objects.filter(related_institution_id__in=subs_akademie)


class WahlIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    start_date = indexes.DateField(null=True, model_attr="start_date")
    membership_id = indexes.IntegerField(null=True)
    membership_type = indexes.CharField(null=True)
    klasse = indexes.CharField(null=True)
    elected = indexes.BooleanField()
    elected_person = indexes.CharField(model_attr="related_personA")
    elected_person_id = indexes.IntegerField(model_attr="related_personA_id")
    elected_by = indexes.CharField(model_attr="related_personB")
    elected_by_id = indexes.IntegerField(model_attr="related_personB_id")

    def get_model(self):
        return PersonPerson

    def index_queryset(self, using=None):
        self.get_model().objects.filter(relation_type_id__in=classes["vorschlag"][0])

    def prepare_membership_id(self, obj):
        pi = PersonInstitution.objects.filter(
            related_person_id=obj.related_personA_id,
            related_institution_id__in=[2, 3, 500],
            start_date_written__contains=obj.start_date_written,
        )
        if pi.count() == 1:
            self.pi = pi
            return pi.pk
        else:
            return None

    def prepare_membership(self, obj):
        if hasattr(self, "pi"):
            pi = self.pi
        else:
            pi = PersonInstitution.objects.filter(
                related_person_id=obj.related_personA_id,
                related_institution_id__in=[2, 3, 500],
                start_date_written__contains=obj.start_date_written,
            )
        if pi.count() == 1:
            if not hasattr(self, "pi"):
                self.pi = pi
            mb = get_mitgliedschaft_from_relation(pi.relation_type, abbreviate=False)
            return mb
        else:
            return None

    def prepare_klasse(self, obj):
        if hasattr(self, "pi"):
            pi = self.pi
        else:
            pi = PersonInstitution.objects.filter(
                related_person_id=obj.related_personA_id,
                related_institution_id__in=[2, 3, 500],
                start_date_written__contains=obj.start_date_written,
            )
        if pi.count() == 1:
            if not hasattr(self, "pi"):
                self.pi = pi
            res = (
                f"{pi.related_institution.name} ({abbreviate(pi.related_institution)})"
            )
            return res
        else:
            return None

    def prepare_elected(self, obj):
        if hasattr(self, "pi"):
            pi = self.pi
        else:
            pi = PersonInstitution.objects.filter(
                related_person_id=obj.related_personA_id,
                related_institution_id__in=[2, 3, 500],
                start_date_written__contains=obj.start_date_written,
            )
        if pi.count() == 1:
            if not hasattr(self, "pi"):
                self.pi = pi
            return True
        else:
            return False


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(boost=2)
    academy_member = indexes.BooleanField(default=False)
    birth_date = indexes.DateField(model_attr="start_date", null=True, faceted=True)
    death_date = indexes.DateField(model_attr="end_date", null=True, faceted=True)
    birth_date_show = indexes.CharField(model_attr="start_date_written", null=True)
    death_date_show = indexes.CharField(model_attr="end_date_written", null=True)
    place_of_birth = indexes.CharField(null=True, faceted=True, boost=1.5)
    place_of_death = indexes.CharField(null=True, faceted=True, boost=1.5)
    gender = indexes.CharField(null=True, model_attr="gender", faceted=True)
    profession = indexes.MultiValueField(null=True, faceted=True)
    comissions = indexes.MultiValueField(null=True, faceted=True)
    education = indexes.MultiValueField(null=True, faceted=True)
    career = indexes.MultiValueField(null=True, faceted=True)
    comissions_show = indexes.MultiValueField(null=True)
    education_show = indexes.MultiValueField(null=True)
    career_show = indexes.MultiValueField(null=True)

    def get_model(self):
        return Person

    def prepare_name(self, object):
        return str(object)

    def prepare_text(self, object):
        txt_types = getattr(settings, "APIS_SEARCH_TEXTTYPES", [])
        res = {"first_name": object.first_name, "name": object.name}
        alt_names = getattr(settings, "APIS_ALTERNATIVE_NAMES", [])
        alt_names_qs = LabelType.objects.filter(name__in=alt_names)
        res["alternative_names"] = [
            alt.label
            for alt in Label.objects.filter(
                temp_entity=object, label_type__in=alt_names_qs
            )
        ]
        res["texts"] = []
        for txt in object.text.filter(kind__name__in=txt_types):
            res["texts"].append(txt.text)
        return res

    def prepare_academy_member(self, object):
        mem_types = getattr(settings, "APIS_SEARCH_ACADEMY_MEMBER")
        academy = getattr(settings, "APIS_SEARCH_ACADEMY")
        if isinstance(mem_types[0], int):
            q = {"relation_type_id__in": mem_types}
        else:
            q = {"relation_type__name__in": mem_types}
        if isinstance(academy[0], int):
            q = {"related_institution_id__in": academy}
        else:
            q = {"related_institution__name__in": academy}
        q["related_person"] = object
        if PersonInstitution.objects.filter(**q).count() > 0:
            return True
        else:
            return False

    def extract_relations(self, object, relation, rel_types, show=True):
        res = []
        rel_obj = relation.replace("person", "")
        exclude_names = getattr(settings, "APIS_SEARCH_EXCLUDE_NAMES", [])
        for r1 in getattr(object, f"{relation}_set").all():
            rel_obj_name = getattr(r1, f"related_{rel_obj}").name
            test_name = True
            for excld in exclude_names:
                if excld in rel_obj_name:
                    test_name = False
            if not test_name:
                continue
            lst_lbls = [y.strip() for y in r1.relation_type.label.split(">>")]
            for l in lst_lbls:
                if l in rel_types:
                    if rel_obj_name not in res:
                        res.append(rel_obj_name)
        return res

    def prepare_profession(self, object):
        return [x.label for x in object.profession.all()]

    def prepare_place_of_birth(self, object):
        rel = object.personplace_set.filter(
            relation_type__name=getattr(settings, "BIRTH_REL_NAME", "geboren in")
        )
        if rel.count() == 1:
            return rel[0].related_place.name
        else:
            return None

    def prepare_place_of_death(self, object):
        rel = object.personplace_set.filter(
            relation_type__name=getattr(settings, "DEATH_REL_NAME", "gestorben in")
        )
        if rel.count() == 1:
            return rel[0].related_place.name
        else:
            return None

    def prepare_education(self, object):
        lst_edu = getattr(settings, "APIS_SEARCH_EDUCATION", [])
        res = self.extract_relations(object, "personinstitution", lst_edu, show=False)
        res.extend(self.extract_relations(object, "personplace", lst_edu, show=False))
        return res

    def prepare_education_show(self, object):
        lst_edu = getattr(settings, "APIS_SEARCH_EDUCATION", [])
        res = self.extract_relations(object, "personinstitution", lst_edu, show=True)
        res.extend(self.extract_relations(object, "personplace", lst_edu, show=True))
        return res

    def prepare_career(self, object):
        lst_career = getattr(settings, "APIS_SEARCH_CAREER", [])
        res = self.extract_relations(
            object, "personinstitution", lst_career, show=False
        )
        res.extend(
            self.extract_relations(object, "personplace", lst_career, show=False)
        )
        return res

    def prepare_career_show(self, object):
        lst_career = getattr(settings, "APIS_SEARCH_CAREER", [])
        res = self.extract_relations(object, "personinstitution", lst_career, show=True)
        res.extend(self.extract_relations(object, "personplace", lst_career, show=True))
        return res

    def prepare_comissions(self, object):
        lst_career = getattr(settings, "APIS_SEARCH_COMISSIONS", [])
        res = self.extract_relations(
            object, "personinstitution", lst_career, show=False
        )
        return res

    def prepare_comissions_show(self, object):
        lst_career = getattr(settings, "APIS_SEARCH_COMISSIONS", [])
        res = self.extract_relations(object, "personinstitution", lst_career, show=True)
        return res

    def index_queryset(self, using=None):
        return oebl_persons


class PersonIndexNew(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(boost=2)
    academy_member = indexes.BooleanField(default=False)
    birth_date = indexes.DateField(model_attr="start_date", null=True, faceted=True)
    death_date = indexes.DateField(model_attr="end_date", null=True, faceted=True)
    birth_date_show = indexes.CharField(model_attr="start_date_written", null=True)
    death_date_show = indexes.CharField(model_attr="end_date_written", null=True)
    place_of_birth = indexes.CharField(null=True, faceted=True, boost=1.5)
    place_of_death = indexes.CharField(null=True, faceted=True, boost=1.5)
    gender = indexes.CharField(null=True, model_attr="gender", faceted=True)
    profession = indexes.MultiValueField(null=True, faceted=True)
    akademiemitgliedschaft = indexes.MultiValueField(null=True, faceted=True)

    def prepare_akademiemitgliedschaft(self, object):
        res = object.personinstitution_set.filter(
            related_institution_id__in=[2, 3, 500],
            relation_type_id__in=classes["mitgliedschaft"][0],
        )
        res_fin = []
        for mitglied in res:
            mitgliedschaft = get_mitgliedschaft_from_relation(mitglied.relation_type)
            res_fin.append(
                f"{mitgliedschaft}__{str(mitglied.related_institution)}__{mitglied.start_date}__{mitglied.start_date}"
            )
        return res_fin

    def prepare_profession(self, object):
        return [x.label for x in object.profession.all()]

    def prepare_place_of_birth(self, object):
        rel = object.personplace_set.filter(
            relation_type__name=getattr(settings, "BIRTH_REL_NAME", "geboren in")
        )
        if rel.count() == 1:
            return rel[0].related_place.name
        else:
            return None

    def prepare_place_of_death(self, object):
        rel = object.personplace_set.filter(
            relation_type__name=getattr(settings, "DEATH_REL_NAME", "gestorben in")
        )
        if rel.count() == 1:
            return rel[0].related_place.name
        else:
            return None

    def prepare_academy_member(self, object):
        mem_types = getattr(settings, "APIS_SEARCH_ACADEMY_MEMBER")
        academy = getattr(settings, "APIS_SEARCH_ACADEMY")
        if isinstance(mem_types[0], int):
            q = {"relation_type_id__in": mem_types}
        else:
            q = {"relation_type__name__in": mem_types}
        if isinstance(academy[0], int):
            q = {"related_institution_id__in": academy}
        else:
            q = {"related_institution__name__in": academy}
        q["related_person"] = object
        if PersonInstitution.objects.filter(**q).count() > 0:
            return True
        else:
            return False

    def prepare_name(self, object):
        return str(object)

    def prepare_text(self, object):
        txt_types = getattr(settings, "APIS_SEARCH_TEXTTYPES", [])
        res = {"first_name": object.first_name, "name": object.name}
        alt_names = getattr(settings, "APIS_ALTERNATIVE_NAMES", [])
        alt_names_qs = LabelType.objects.filter(name__in=alt_names)
        res["alternative_names"] = [
            alt.label
            for alt in Label.objects.filter(
                temp_entity=object, label_type__in=alt_names_qs
            )
        ]
        res["texts"] = []
        for txt in object.text.filter(kind__name__in=txt_types):
            res["texts"].append(txt.text)
        return res