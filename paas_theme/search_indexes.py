from haystack import indexes
from django.conf import settings

from apis_core.apis_metainfo.models import Collection, Text
from apis_core.apis_vocabularies.models import (
    LabelType,
    PersonInstitutionRelation,
    PersonPlaceRelation,
    ProfessionType,
)
from apis_core.apis_labels.models import Label
from apis_core.apis_entities.models import Person, Institution, Place
from apis_core.apis_relations.models import PersonInstitution, PersonPerson, PersonEvent
from .provide_data import (
    get_child_classes,
    get_child_institutions_from_parent,
    get_mitgliedschaft_from_relation,
    abbreviate,
)
from .provide_data import classes

coll_id = 2

map_classes_pr_labels = {
    "Habilitation": classes["habilitation"],
    "Promotion": classes["promotion_inst_ids"],
    "Akademieinstitution": classes["akad_funktionen"]["obfrau/obmann"][0]
    + classes["akad_funktionen"]["mitglied kommission"][0]
    + classes["akad_funktionen"]["direktorin institut"][0]
    + classes["akad_funktionen"]["kuratorium"][0],
    "Beruf": [
        item for sublist in classes["berufslaufbahn_map"].values() for item in sublist
    ],
}


class PersonProfessionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr="label")
    label_auto = indexes.EdgeNgramField()
    name = indexes.CharField(model_attr="name")
    name_auto = indexes.EdgeNgramField(model_attr="name")
    kind = indexes.CharField(null=True)

    def get_model(self):
        return ProfessionType

    def prepare_label_auto(self, object):
        return " ".join([x.strip() for x in object.label.split(">>")])

    def prepare_kind(self, object):
        for k, v in map_classes_pr_labels.items():
            if object.pk in v:
                return k
        return None


class PersonInstitutionRelationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr="label")
    label_auto = indexes.EdgeNgramField()
    name = indexes.CharField(model_attr="name")
    name_auto = indexes.EdgeNgramField(model_attr="name")
    kind = indexes.CharField(null=True)

    def get_model(self):
        return PersonInstitutionRelation

    def prepare_label_auto(self, object):
        return " ".join([x.strip() for x in object.label.split(">>")])

    def prepare_kind(self, object):
        for k, v in map_classes_pr_labels.items():
            if object.pk in v:
                return k
        return None


class PlaceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    kind = indexes.CharField(model_attr="kind__label", null=True)
    name_auto = indexes.EdgeNgramField(model_attr="name")
    location = indexes.LocationField(null=True)
    relation_types_person_id = indexes.MultiValueField(null=True)

    def get_model(self):
        return Place

    def prepare_relation_types_person_id(self, object):
        res = []
        for pi in object.personplace_set.all():
            if pi.relation_type_id not in res:
                res.append(pi.relation_type_id)
        return res

    def prepare_location(self, object):
        if object.lat and object.lng:
            return f"{object.lat},{object.lng}"
        else:
            return None

    def prepare_text(self, object):
        res = {"name": object.name}
        alt_names = getattr(settings, "APIS_ALTERNATIVE_NAMES", [])
        alt_names_qs = LabelType.objects.filter(name__in=alt_names)
        res["alternative_names"] = [
            alt.label
            for alt in Label.objects.filter(
                temp_entity=object, label_type__in=alt_names_qs
            )
        ]
        return res


class InstitutionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    academy = indexes.BooleanField(default=False)
    kind = indexes.CharField(model_attr="kind__label", null=True)
    start_date = indexes.DateField(model_attr="start_date", null=True)
    end_date = indexes.DateField(model_attr="end_date", null=True)
    name_auto = indexes.EdgeNgramField(model_attr="name")
    relation_types_person_id = indexes.MultiValueField(null=True)
    # located_in = indexes.CharField(null=True)
    # located_in_id = indexes.IntegerField(null=True)
    # located_at = indexes.LocationField(null=True)

    def get_model(self):
        return Institution

    def prepare_relation_types_person_id(self, object):
        res = []
        for pi in object.personinstitution_set.all():
            if pi.relation_type_id not in res:
                res.append(pi.relation_type_id)
        return res

    def prepare_academy(self, object):
        return object.pk in classes["subs_akademie"]

    def prepare_text(self, object):
        res = {"name": object.name}
        alt_names = getattr(settings, "APIS_ALTERNATIVE_NAMES", [])
        alt_names_qs = LabelType.objects.filter(name__in=alt_names)
        res["alternative_names"] = [
            alt.label
            for alt in Label.objects.filter(
                temp_entity=object, label_type__in=alt_names_qs
            )
        ]
        return res

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class FunktionenAkademieIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    field = indexes.CharField()
    person = indexes.CharField(model_attr="related_person")
    person_id = indexes.IntegerField(model_attr="related_person_id")
    start_date = indexes.DateField(model_attr="start_date", null=True)
    relation_type_id = indexes.IntegerField(model_attr="relation_type_id")
    relation_type = indexes.CharField(model_attr="relation_type")
    relation_type_full = indexes.CharField(model_attr="relation_type")
    relation_type_mapped = indexes.MultiValueField(null=True)
    end_date = indexes.DateField(model_attr="end_date", null=True)
    institution_id = indexes.IntegerField(model_attr="related_institution_id")
    institution = indexes.CharField(model_attr="related_institution")
    institution_type = indexes.CharField(model_attr="related_institution__kind__name")

    def get_model(self):
        return PersonInstitution

    def prepare_relation_type_mapped(self, object):
        res = []
        for key, value in classes["berufslaufbahn_map"].items():
            if object.relation_type_id in value and key not in res:
                res.append(key)
        return res

    def prepare_field(self, object):
        if object.related_institution_id in classes["subs_akademie"]:
            return "Funktionen in Akademieinstitutionen"
        else:
            return "Berufliche Position"

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(related_person__collection__id=coll_id)


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
    elected_by_gender = indexes.CharField(
        null=True, model_attr="related_personB__gender"
    )
    elected_by_profession = indexes.MultiValueField(null=True)

    def get_model(self):
        return PersonPerson

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            relation_type_id__in=classes["vorschlag"][0],
            related_personA__collection__id=coll_id,
        )

    def prepare_elected_by_profession(self, object):
        return [x.label for x in object.related_personB.profession.all()]

    def prepare_membership_id(self, obj):
        qdict = {
            "related_person_id": obj.related_personA_id,
            "related_institution_id__in": [2, 3, 500],
        }
        if obj.start_date_written is not None:
            qdict["start_date_written__contains"] = obj.start_date_written
        pi = PersonInstitution.objects.filter(**qdict)
        if pi.count() == 1:
            self.pi = pi
            return pi[0].pk
        else:
            return None

    def prepare_membership(self, obj):
        if hasattr(self, "pi"):
            pi = self.pi
        else:
            qdict = {
                "related_person_id": obj.related_personA_id,
                "related_institution_id__in": [2, 3, 500],
            }
            if obj.start_date_written is not None:
                qdict["start_date_written__contains"] = obj.start_date_written
            pi = PersonInstitution.objects.filter(**qdict)
        if pi.count() == 1:
            if not hasattr(self, "pi"):
                self.pi = pi
            mb = get_mitgliedschaft_from_relation(pi[0].relation_type, abbreviate=False)
            return mb
        else:
            return None

    def prepare_klasse(self, obj):
        if hasattr(self, "pi"):
            pi = self.pi
        else:
            qdict = {
                "related_person_id": obj.related_personA_id,
                "related_institution_id__in": [2, 3, 500],
            }
            if obj.start_date_written is not None:
                qdict["start_date_written__contains"] = obj.start_date_written
            pi = PersonInstitution.objects.filter(**qdict)
        if pi.count() == 1:
            if not hasattr(self, "pi"):
                self.pi = pi
            res = f"{pi[0].related_institution.name} ({abbreviate(pi[0].related_institution)})"
            return res
        else:
            return None

    def prepare_elected(self, obj):
        if hasattr(self, "pi"):
            pi = self.pi
        else:
            qdict = {
                "related_person_id": obj.related_personA_id,
                "related_institution_id__in": [2, 3, 500],
            }
            if obj.start_date_written is not None:
                qdict["start_date_written__contains"] = obj.start_date_written
            pi = PersonInstitution.objects.filter(**qdict)
        if pi.count() == 1:
            if not hasattr(self, "pi"):
                self.pi = pi
            return True
        else:
            return False


""" class PersonIndex(indexes.SearchIndex, indexes.Indexable):
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
        return oebl_persons """


class PersonIndexNew(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    name = indexes.CharField()
    academy_member = indexes.BooleanField(default=False)
    birth_date = indexes.DateField(model_attr="start_date", null=True, faceted=True)
    death_date = indexes.DateField(model_attr="end_date", null=True, faceted=True)
    birth_date_show = indexes.CharField(model_attr="start_date_written", null=True)
    death_date_show = indexes.CharField(model_attr="end_date_written", null=True)
    place_of_birth = indexes.CharField(null=True, faceted=True)
    place_of_birth_id = indexes.IntegerField(null=True)
    place_of_death = indexes.CharField(null=True, faceted=True)
    place_of_death_id = indexes.IntegerField(null=True)
    klasse_person = indexes.CharField(null=True, faceted=True)
    gender = indexes.CharField(null=True, model_attr="gender", faceted=True)
    profession = indexes.MultiValueField(null=True, faceted=True)
    profession_id = indexes.MultiValueField(null=True)
    akademiemitgliedschaft = indexes.MultiValueField(null=True, faceted=True)
    mitgliedschaft_short = indexes.CharField(null=True, faceted=True)
    funk_praesidentin = indexes.BooleanField(default=False)
    funk_vizepraesidentin = indexes.BooleanField(default=False)
    funk_generalsekretaerin = indexes.BooleanField(default=False)
    funk_sekretaerin = indexes.BooleanField(default=False)
    funk_klassenpres_math_nat = indexes.BooleanField(default=False)
    funk_klassenpres_phils_hist = indexes.BooleanField(default=False)
    funk_sekretaerin = indexes.BooleanField(default=False)
    funk_obfrau = indexes.BooleanField(default=False)
    funk_mitgl_kommission = indexes.BooleanField(default=False)
    funk_direkt_forsch_inst = indexes.BooleanField(default=False)
    funk_obfrau_kurat = indexes.BooleanField(default=False)
    akademiefunktionen = indexes.MultiValueField(null=True, faceted=True)
    akademiepreise = indexes.MultiValueField(null=True, faceted=True)
    preisfragen = indexes.MultiValueField(null=True, faceted=True)
    nobelpreis = indexes.BooleanField(default=False)
    ewk = indexes.BooleanField(default=False)
    schule = indexes.MultiValueField(null=True, faceted=True)
    schule_id = indexes.MultiValueField(null=True)
    universitaet = indexes.MultiValueField(null=True, faceted=True)
    universitaet_id = indexes.MultiValueField(null=True, faceted=True)
    uni_habilitation = indexes.MultiValueField(null=True, faceted=True)
    uni_habilitation_id = indexes.MultiValueField(null=True)
    fach_habilitation = indexes.MultiValueField(null=True, faceted=True)
    fach_habilitation_id = indexes.MultiValueField(null=True)
    w_austausch = indexes.MultiValueField(null=True, faceted=True)
    w_austausch_id = indexes.MultiValueField(null=True)
    mitglied_nsdap = indexes.BooleanField(default=False)

    def get_model(self):
        return Person

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(collection__id=coll_id)

    def prepare_schule(self, object):
        return list(
            object.personinstitution_set.filter(relation_type_id__in=[176]).values_list(
                "related_institution__name", flat=True
            )
        )

    def prepare_schule_id(self, object):
        return list(
            object.personinstitution_set.filter(relation_type_id__in=[176]).values_list(
                "related_institution_id", flat=True
            )
        )

    def prepare_universitaet(self, object):
        return list(
            set(
                object.personinstitution_set.filter(
                    relation_type_id__in=[1369, 1371] + classes["promotion_inst_ids"]
                ).values_list("related_institution__name", flat=True)
            )
        )

    def prepare_universitaet_id(self, object):
        return list(
            set(
                object.personinstitution_set.filter(
                    relation_type_id__in=[1369, 1371] + classes["promotion_inst_ids"]
                ).values_list("related_institution_id", flat=True)
            )
        )

    def prepare_uni_habilitation(self, object):
        return list(
            (
                object.personinstitution_set.filter(
                    relation_type_id__in=classes["habilitation"]
                ).values_list("related_institution__name", flat=True)
            )
        )

    def prepare_uni_habilitation_id(self, object):
        return list(
            (
                object.personinstitution_set.filter(
                    relation_type_id__in=classes["habilitation"]
                ).values_list("related_institution_id", flat=True)
            )
        )

    def prepare_fach_habilitation(self, object):
        return list(
            set(
                [
                    x.relation_type.label.split(">>")[-1].strip()
                    for x in object.personinstitution_set.filter(
                        relation_type_id__in=classes["habilitation"]
                    )
                ]
            )
        )

    def prepare_fach_habilitation_id(self, object):
        return list(
            set(
                [
                    x.relation_type_id
                    for x in object.personinstitution_set.filter(
                        relation_type_id__in=classes["habilitation"]
                    )
                ]
            )
        )

    def prepare_w_austausch(self, object):
        return list(
            set(
                object.personplace_set.filter(relation_type_id=3375).values_list(
                    "related_place__name", flat=True
                )
            )
        )

    def prepare_w_austausch_id(self, object):
        return list(
            set(
                object.personplace_set.filter(relation_type_id=3375).values_list(
                    "related_place_id", flat=True
                )
            )
        )

    def prepare_mitglied_nsdap(self, object):
        return (
            object.personinstitution_set.filter(
                relation_type_id=3451, related_institution_id=49596
            ).count()
            == 1
        )

    def prepare_nobelpreis(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution_id__in=[51502, 44859, 45721], relation_type_id=138
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_ewk(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution_id__in=[29953], relation_type_id=138
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_akademiepreise(self, object):
        res = [
            pi.related_institution.name
            for pi in PersonInstitution.objects.filter(
                related_person=object,
                related_institution_id__in=classes["akademiepreise"],
                relation_type_id=138,
            )
        ]
        return res

    def prepare_preisaufgaben(self, object):
        res = [
            pi.related_event.name
            for pi in PersonEvent.objects.filter(
                related_person=object,
                related_event_id__in=classes["preisaufgaben"],
                relation_type_id=143,
            )
        ]
        return res

    def prepare_funk_praesidentin(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution_id=500,
                relation_type_id__in=classes["akad_funktionen"]["präsidentin"][0],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_vizepraesidentin(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution_id=500,
                relation_type_id__in=classes["akad_funktionen"]["vizepräsidentin"][0],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_generalsekretaerin(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution_id=500,
                relation_type_id__in=classes["akad_funktionen"]["generalsekretärin"][0],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_sekretaerin(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution_id=500,
                relation_type_id__in=classes["akad_funktionen"]["sekretärin"][0],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_obfrau(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution__kind_id=82,
                relation_type_id__in=classes["akad_funktionen"]["obfrau/obmann"][0],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_mitgl_kommission(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution__kind_id=82,
                relation_type_id__in=classes["akad_funktionen"]["mitglied kommission"][
                    0
                ],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_direkt_forsch_inst(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution__kind_id__in=[83, 84],
                relation_type_id__in=classes["akad_funktionen"]["direktorin institut"][
                    0
                ],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_obfrau_kurat(self, object):
        if (
            object.personinstitution_set.filter(
                related_institution__kind_id__in=[83, 84],
                relation_type_id__in=classes["akad_funktionen"]["kuratorium"][0],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_funk_klassenpres_math_nat(self, object):
        return (
            object.personinstitution_set.filter(
                relation_type_id__in=classes["akad_funktionen"]["präsidentin"][0],
                related_institution_id=3,
            ).count()
            > 0
        )

    def prepare_funk_klassenpres_phils_hist(self, object):
        return (
            object.personinstitution_set.filter(
                relation_type_id__in=classes["akad_funktionen"]["präsidentin"][0],
                related_institution_id=2,
            ).count()
            > 0
        )

    def prepare_akademiefunktionen(self, object):
        res = []
        rel_type_ids = []
        for k, rel_types in classes["akad_funktionen"].items():
            rel_type_ids.extend(rel_types[0])
        for rel in object.personinstitution_set.filter(
            related_institution_id__in=classes["subs_akademie"],
            relation_type_id__in=rel_type_ids,
        ):
            res.append(
                f"{str(rel.related_institution)}__{rel.relation_type.label}__{rel.start_date}__{rel.end_date}"
            )
        return res

    def prepare_akademiemitgliedschaft(self, object):
        res = object.personinstitution_set.filter(
            related_institution_id__in=[2, 3, 500],
            relation_type_id__in=classes["mitgliedschaft"][0],
        )
        res_fin = []
        for mitglied in res:
            mitgliedschaft = get_mitgliedschaft_from_relation(mitglied.relation_type)
            res_fin.append(mitgliedschaft)
        return list(set(res_fin))

    def prepare_klasse_person(self, object):
        res = object.personinstitution_set.filter(
            related_institution_id__in=[2, 3, 500],
            relation_type_id__in=classes["mitgliedschaft"][0],
        )
        if res.count() > 0:
            return str(res[0].related_institution)
        else:
            return None

    def prepare_mitgliedschaft_short(self, object):
        res = object.personinstitution_set.filter(
            related_institution_id__in=[2, 3, 500],
            relation_type_id__in=classes["mitgliedschaft"][0],
        )
        res_fin = []
        for mitglied in res:
            mitgliedschaft = get_mitgliedschaft_from_relation(mitglied.relation_type)
            res_fin.append(mitgliedschaft)
        for m in classes["mitgliedschaft sortiert"]:
            if m in res_fin:
                return m
        return None

    def prepare_profession(self, object):
        return [x.label for x in object.profession.all()]

    def prepare_profession_id(self, object):
        return [x.pk for x in object.profession.all()]

    def prepare_place_of_birth(self, object):
        birth_rel = getattr(settings, "BIRTH_REL_NAME", [])
        if isinstance(birth_rel, str):
            birth_rel = PersonPlaceRelation.objects.filter(name=birth_rel).values_list(
                "pk", flat=True
            )
        rel = object.personplace_set.filter(relation_type_id__in=birth_rel)
        if rel.count() == 1:
            return rel[0].related_place.name
        else:
            return None

    def prepare_place_of_birth_id(self, object):
        birth_rel = getattr(settings, "BIRTH_REL_NAME", [])
        if isinstance(birth_rel, str):
            birth_rel = PersonPlaceRelation.objects.filter(name=birth_rel).values_list(
                "pk", flat=True
            )
        rel = object.personplace_set.filter(relation_type_id__in=birth_rel)
        if rel.count() == 1:
            return rel[0].related_place_id
        else:
            return None

    def prepare_place_of_death(self, object):
        death_rel = getattr(settings, "DEATH_REL_NAME", [])
        if isinstance(death_rel, str):
            death_rel = PersonPlaceRelation.objects.filter(name=death_rel).values_list(
                "pk", flat=True
            )
        rel = object.personplace_set.filter(relation_type_id__in=death_rel)
        if rel.count() == 1:
            return rel[0].related_place.name
        else:
            return None

    def prepare_place_of_death_id(self, object):
        death_rel = getattr(settings, "DEATH_REL_NAME", [])
        if isinstance(death_rel, str):
            death_rel = PersonPlaceRelation.objects.filter(name=death_rel).values_list(
                "pk", flat=True
            )
        rel = object.personplace_set.filter(relation_type_id__in=death_rel)
        if rel.count() == 1:
            return rel[0].related_place_id
        else:
            return None

    def prepare_academy_member(self, object):
        if (
            object.personinstitution_set.filter(
                relation_type_id__in=classes["mitgliedschaft"][0],
                related_institution_id__in=[2, 3, 500],
            ).count()
            > 0
        ):
            return True
        else:
            return False

    def prepare_name(self, object):
        return str(object)

    def prepare_text(self, object):
        lst_fields = [
            "name",
            "academy_member",
            "place_of_death",
            "place_of_birth",
            "profession",
            "akademiemitgliedschaft",
            "akademiefunktionen",
            "funk_obfrau_kurat",
            "funk_direkt_forsch_inst",
            "funk_mitgl_kommission",
            "funk_obfrau",
            "funk_sekretaerin",
            "funk_generalsekretaerin",
            "funk_vizepraesidentin",
            "funk_praesidentin",
            "preisaufgaben",
            "akademiepreise",
            "ewk",
            "nobelpreis",
        ]
        res = []
        bool_map = {
            "ewk": "Preisträger Österreichisches Ehrenzeichen für Wissenschaft und Kunst",
            "nobelpreis": "Nobelpreisträger",
            "funk_praesidentin": "Präsident",
            "funk_vizepraesidentin": "Vizepräsident",
            "funk_generalsekretaerin": "Generalsekretär",
            "funk_obfrau": "Obmann Obfrau",
            "funk_mitgl_kommission": "Mitglied Kommission",
            "funk_direkt_forsch_inst": "Direktor Direktorin Institut",
            "funk_obfrau_kurat": "Obmann Obfrau",
            "academy_member": "Mitglied Akademie",
        }
        for field in lst_fields:
            ret = getattr(self, f"prepare_{field}")(object)
            if isinstance(ret, str):
                res.append(ret)
            elif isinstance(ret, list):
                res.extend(ret)
            elif isinstance(ret, bool):
                if field in bool_map.keys():
                    res.append(bool_map[field])
                else:
                    res.append(field)
        return "\n".join(res)
