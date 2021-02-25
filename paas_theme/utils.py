from datetime import date, timedelta
import glob
import re

from django.conf import settings
from django.db.models import Q

from apis_core.apis_entities.models import Person
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Collection
from apis_core.apis_relations.models import PersonPlace

from apis_core.apis_vocabularies.models import (
    PersonPersonRelation,
    PersonEventRelation,
    PersonInstitutionRelation,
    PersonPlaceRelation,
    PersonWorkRelation,
)


try:
    FEATURED_COLLECTION_NAME = settings.FEATURED_COLLECTION_NAME
except AttributeError:
    FEATURED_COLLECTION_NAME = None

try:
    BIRTH_REL_NAME = settings.BIRTH_REL_NAME
except AttributeError:
    BIRTH_REL_NAME = None

try:
    DEATH_REL_NAME = settings.DEATH_REL_NAME
except AttributeError:
    DEATH_REL_NAME = None

try:
    MAIN_TEXT = settings.MAIN_TEXT_NAME
except AttributeError:
    MAIN_TEXT = None


def get_child_classes(objids, obclass):
    """used to retrieve a list of primary keys of sub classes"""
    for obj in objids:
        obj = obclass.objects.get(pk=obj)
        p_class = list(obj.vocabsbaseclass_set.all())
        p = p_class.pop() if len(p_class) > 0 else False
        while p:
            if p.pk not in objids:
                objids.append(p.pk)
            p_class += list(p.vocabsbaseclass_set.all())
            p = p_class.pop() if len(p_class) > 0 else False
    return objids


def get_main_text(MAIN_TEXT):
    if MAIN_TEXT is not None:
        return MAIN_TEXT
    else:
        return None


def abbreviate(value):
    print(value.name)
    if value.name == "MATHEMATISCH-NATURWISSENSCHAFTLICHE KLASSE":
        return "mn. K."
    elif value.name == "PHILOSOPHISCH-HISTORISCHE KLASSE":
        return "ph. K."
    else:
        return value


def enrich_person_context(person_object, context):
    if BIRTH_REL_NAME is not None:
        try:
            if isinstance(BIRTH_REL_NAME, list):
                qdict = {"relation_type_id__in": BIRTH_REL_NAME}
            elif isinstance(BIRTH_REL_NAME, str):
                qdict = {"relation_type__name": BIRTH_REL_NAME}
            context["place_of_birth"] = (
                person_object.personplace_set.filter(**qdict).first().related_place
            )
        except AttributeError:
            context["place_of_birth"] = None
    else:
        context["place_of_birth"] = "Please define place of birth variable"
    if DEATH_REL_NAME is not None:
        try:
            if isinstance(DEATH_REL_NAME, list):
                qdict = {"relation_type_id__in": DEATH_REL_NAME}
            elif isinstance(DEATH_REL_NAME, str):
                qdict = {"relation_type__name": DEATH_REL_NAME}
            context["place_of_death"] = (
                person_object.personplace_set.filter(**qdict).first().related_place
            )
        except AttributeError:
            context["place_of_death"] = None
    else:
        context["place_of_death"] = "Please define place of death variable"
    try:
        context["profession"] = ", ".join(
            person_object.profession.all().values_list("name", flat=True)
        )

    except AttributeError:
        context["profession"] = None
    try:
        if person_object.profession.all().count() > 1:
            context["profession_categories"] = person_object.profession.all()[
                : person_object.profession.all().count() - 1
            ]
    except AttributeError:
        context["profession_categories"] = None
    try:
        context[
            "related_institutions"
        ] = person_object.personinstitution_set.all().filter_for_user()
    except AttributeError:
        context["related_institutions"] = None
    context["normdaten"] = []
    normdaten = person_object.uri_set.filter(uri__contains="d-nb.info")
    if normdaten.count() > 0:
        for uri in normdaten:
            context["normdaten"].append(uri.uri)
    cv_de = person_object.text.filter(
        kind__name=getattr(settings, "PAAS_CV_DE", "Curriculum Vitae (de)")
    )
    if cv_de.count() == 1:
        context["cv_de"] = cv_de[0].text
    else:
        context["cv_de"] = ""
    cv_en = person_object.text.filter(
        kind__name=getattr(settings, "PAAS_CV_EN", "Curriculum Vitae (en)")
    )
    if cv_en.count() == 1:
        context["cv_en"] = cv_en[0].text
    else:
        context["cv_en"] = ""
    lst_images = glob.glob(
        getattr(settings, "BASE_DIR") + "/member_images/" + f"/{person_object.pk}.*"
    )
    if len(lst_images) == 1:
        context["image"] = lst_images[0].split("/")[-1]
    else:
        context["image"] = False
    context["mitgliedschaften"] = []
    rel_test = []
    for rel in person_object.personinstitution_set.filter(
        related_institution_id__in=[2, 3, 500],
        relation_type_id__in=[
            33,
            34,
            35,
            36,
            45,
            46,
            47,
            48,
            50,
            52,
            53,
            54,
            56,
            57,
            58,
            59,
        ],
    ).order_by("start_date"):
        r_lbl = re.search("\((.+)\)", rel.relation_type.label.split(" >> ")[1]).group(1)
        if r_lbl not in rel_test:
            context["mitgliedschaften"].append(
                f"<span title='{rel.relation_type.label.split(' >> ')[1]}' style='text-decoration: underline'>{r_lbl}</span> in <span title='{rel.related_institution}' style='text-decoration: underline'>{abbreviate(rel.related_institution)}</span> ({rel.start_date_written}{'-'+rel.end_date_written if rel.end_date_written else ''})"
            )
            rel_test.append(r_lbl)
    context["rel_dict_weg_zur_akademie"] = {
        "herkunft": [
            f'{rel.relation_type.label} <a href="place/{rel.related_place_id}">{rel.related_place}</a> ({rel.start_date_written})'
            for rel in person_object.personplace_set.filter(
                relation_type_id__in=[64, 152, 3090]
            )
        ],
        "schulbildung": [
            f'{rel.relation_type.label}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written})'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[176]
            )
        ],
        "studium": [
            f'{rel.relation_type.label}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written})'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[1369, 1371, 1389]
            )
        ],
        "berufslaufbahn": [
            f'{rel.relation_type.label}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written})'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[1851, 1385]
            )
        ],
        "wahl_mitgliederstatus": [
            f'{rel.relation_type.label}: <a href="/person/{rel.related_personB_id}">{rel.related_personB}</a> ({rel.start_date_written})'
            for rel in person_object.related_personB.filter(
                relation_type_id__in=get_child_classes(
                    [3061, 3141], PersonPersonRelation
                )
            )
        ]
        + [
            f'{rel.relation_type.label_reverse}: <a href="/person/{rel.related_personA_id}">{rel.related_personA}</a> ({rel.start_date_written})'
            for rel in person_object.related_personA.filter(
                relation_type_id__in=get_child_classes(
                    [3061, 3141], PersonPersonRelation
                )
            )
        ]
        + [
            f'{rel.relation_type.label_reverse}: <a href="/event/{rel.related_event_id}">{rel.related_event}</a> ({rel.start_date_written})'
            for rel in person_object.personevent_set.filter(
                relation_type_id__in=get_child_classes(
                    [3052, 3053], PersonEventRelation
                )
            )
        ]
        + [
            f'{rel.relation_type.label_reverse}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written})'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=get_child_classes([37], PersonInstitutionRelation),
                related_institution_id__in=[2, 3, 500],
            )
        ],
    }
    context["rel_dict_in_akademie"] = {
        "funktionen": [
            f'{rel.relation_type.label}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written})'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=get_child_classes(
                    [117, 112, 1876, 102, 104, 26], PersonInstitutionRelation
                )
            )
        ],
        "wahlvorschläge": [
            f'{rel.relation_type.label_reverse}: <a href="/person/{rel.related_personA_id}">{rel.related_personA}</a> ({rel.start_date_written})'
            for rel in person_object.related_personA.filter(
                relation_type_id__in=get_child_classes([3061], PersonPersonRelation)
            )
        ],
        "mitgliedschaften_in_anderen_akademien": [
            f'{rel.relation_type.label}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written})'
            for rel in person_object.personinstitution_set.filter(
                related_institution__kind_id=3378,
                relation_type_id__in=get_child_classes([37], PersonInstitutionRelation),
            )
        ],
        "akademiepreise": [
            f'{rel.relation_type.label}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written})'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=get_child_classes(
                    [138, 3501], PersonInstitutionRelation
                ),
            ).exclude(related_institution_id__in=[45721, 44859, 51502])
        ],
        "akademieaustausch": [
            f'{rel.relation_type.label} <a href="place/{rel.related_place_id}">{rel.related_place}</a> ({rel.start_date_written})'
            for rel in person_object.personplace_set.filter(
                relation_type_id__in=get_child_classes([3375], PersonPlaceRelation)
            )
        ],
        "nachrufe": [
            f'{rel.relation_type.label} <a href="work/{rel.related_work_id}">{rel.related_work}</a> ({rel.start_date_written})'
            for rel in person_object.personwork_set.filter(
                relation_type_id__in=get_child_classes([146, 147], PersonWorkRelation)
            )
        ],
    }
    return context


def get_featured_person():
    if FEATURED_COLLECTION_NAME is not None:
        return Person.objects.filter(collection__name=FEATURED_COLLECTION_NAME).first()
    else:
        return None


col_oebl = getattr(settings, "APIS_OEBL_BIO_COLLECTION", "ÖBL Biographie")
col_oebl = Collection.objects.filter(name=col_oebl)
if col_oebl.count() == 1:
    oebl_persons = Person.objects.filter(collection=col_oebl[0])
else:
    oebl_persons = Person.objects.all()

# oebl_persons = Person.objects.exclude(Q(text=None) | Q(text__text=""))

oebl_persons_with_date = oebl_persons.exclude(Q(start_date=None) | Q(end_date=None))

person_place_born = PersonPlace.objects.filter(
    relation_type__name__icontains=getattr(settings, "BIRTH_REL_NAME", "birth")
)
person_place_death = PersonPlace.objects.filter(
    relation_type__name__icontains=getattr(settings, "DEATH_REL_NAME", "death")
)

current_date = date.today()
current_date = current_date - timedelta(days=1)
current_day = current_date.day
current_month = current_date.month


def get_born_range():
    oebl_persons_sorted_by_start_date = oebl_persons_with_date.order_by("start_date")
    oldest_person = oebl_persons_sorted_by_start_date.first()
    youngest_person = oebl_persons_sorted_by_start_date.last()
    return [
        oldest_person.start_date if oldest_person else date(1700, 1, 1),
        youngest_person.start_date if youngest_person else date(2000, 1, 1),
    ]


def get_died_range():
    oebl_persons_sorted_by_end_date = oebl_persons_with_date.order_by("end_date")
    person_died_first = oebl_persons_sorted_by_end_date.first()
    person_died_last = oebl_persons_sorted_by_end_date.last()
    return [
        person_died_first.end_date if person_died_first else date(1700, 1, 1),
        person_died_last.end_date if person_died_last else date(2000, 1, 1),
    ]


def get_died_latest():
    person_died_latest = oebl_persons.order_by("-end_date")[1]
    return person_died_latest.end_date


def get_daily_entries(context, qs):
    context["person_born"] = qs.filter(
        start_date__day=current_day, start_date__month=current_month
    )
    context["person_born_count"] = context["person_born"].count()
    context["person_died"] = qs.filter(
        end_date__day=current_day, end_date__month=current_month
    )
    context["person_died_count"] = context["person_died"].count()
    return context
