from haystack import indexes
from django.conf import settings
from django.db.models import Q

from apis_core.apis_metainfo.models import Collection, Text
from apis_core.apis_vocabularies.models import (
    LabelType,
    PersonInstitutionRelation,
    PersonPlaceRelation,
    ProfessionType,
)
from apis_core.apis_labels.models import Label
from apis_core.apis_entities.models import Institution, Place
from apis_core.apis_relations.models import PersonInstitution, PersonPerson, PersonEvent
from paas_theme.models import PAASPerson
from .provide_data import (
    get_child_classes,
    get_child_institutions_from_parent,
    get_mitgliedschaft_from_relation,
    abbreviate,
)
from .provide_data import classes

from .id_mapping import KLASSEN_IDS, NOBEL_PREISE

coll_id = 16

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


class GermanTextField(indexes.CharField):
    field_type = "text_de"


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
    kind = indexes.CharField(model_attr="kind__label", null=True, faceted=True)
    start_date = indexes.DateField(model_attr="start_date", null=True)
    end_date = indexes.DateField(model_attr="end_date", null=True)
    name_auto = indexes.EdgeNgramField(model_attr="name")
    relation_types_person_id = indexes.MultiValueField(null=True)
    mitglieder_id = indexes.MultiValueField(null=True)
    # located_in = indexes.CharField(null=True)
    # located_in_id = indexes.IntegerField(null=True)
    # located_at = indexes.LocationField(null=True)

    institution_art = indexes.IntegerField()
    institution_klasse = indexes.IntegerField()

    def prepare_mitglieder_id(self, object):
        return [p.related_person_id for p in object.personinstitution_set.all()]

    def prepare_kind(self, object):
        if object.kind:
            return object.kind.name
        return 0

    def prepare_institution_art(self, object):
        if object.kind:
            return object.kind.id
        return 0

    def prepare_institution_klasse(self, object):
        klasse_inst = object.related_institutionB.filter(
            relation_type__pk=2, related_institutionB__pk__in=[1, 2, 3, 500, 501, 59131]
        ).first()
        if klasse_inst:
            klasse = klasse_inst.related_institutionB.pk
            # 2 =  Philosophisch-Historische Klasse
            # 3 = Mathematisch-Naturwissenschaftliche Klasse
            if klasse in [2, 3]:
                return klasse
            else:
                # 1 = Andere
                return 1
        # 0 = Nothing, not searchable by klasse
        return 0

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

    # TODO: MAYBE remove GEMEINSAM KOMMISSION etc. (not id__in=[1,2,3])
    def index_queryset(self, using=None):
        qs = self.get_model().objects.filter(Q(kind__parent_class__id=81)|Q(kind_id=137))
        return qs


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
            "related_institution_id__in": KLASSEN_IDS,
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
    gender = indexes.CharField(null=True, faceted=True)
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
        return PAASPerson

    def index_queryset(self, using=None):
        return self.get_model().objects.members()

    def prepare_gender(self, object):
        if object.gender == "male":
            return "männlich"
        elif object.gender == "female":
            return "weiblich"
        else:
            return "unbekannt"

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
        if object.nobelprizes() is None:
            return False
        else:
            return True

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
                related_institution_id__in=classes["akademiepreise"]+[29953],
                relation_type_id=138,
            )
        ]
        nb = object.nobelprizes()
        if nb is not None:
            res.extend([x[1] for x in nb]) 
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
        res_fin = []
        for m in object.get_memberships():
            res_fin.append(m["mitgliedschaft"])
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
        res_fin = []
        for m in object.get_memberships():
            res_fin.append(m["mitgliedschaft"])
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
        return object.is_member()

    def prepare_name(self, object):
        return f"{object.first_name} {object.name}"

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
