from datetime import date, timedelta
import glob
import re

from django.conf import settings
from django.db.models import Q

from apis_core.apis_entities.models import Person
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Collection
from apis_core.apis_relations.models import (
    PersonPlace,
    PersonPerson,
    PersonInstitution,
    InstitutionInstitution,
)

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


def get_child_classes(objids, obclass, labels=False):
    """used to retrieve a list of primary keys of sub classes"""
    if labels:
        labels_lst = []
    for obj in objids:
        obj = obclass.objects.get(pk=obj)
        p_class = list(obj.vocabsbaseclass_set.all())
        p = p_class.pop() if len(p_class) > 0 else False
        while p:
            if p.pk not in objids:
                if labels:
                    labels_lst.append((p.pk, p.label))
                objids.append(p.pk)
            p_class += list(p.vocabsbaseclass_set.all())
            p = p_class.pop() if len(p_class) > 0 else False
    if labels:
        return (objids, labels_lst)
    else:
        return objids


def get_child_institutions_from_parent(insts):
    res = []
    for i in insts:
        res.extend(
            list(
                InstitutionInstitution.objects.filter(
                    related_institutionA_id=i
                ).values_list("related_institutionB_id", flat=True)
            )
        )
    return res


def get_main_text(MAIN_TEXT):
    if MAIN_TEXT is not None:
        return MAIN_TEXT
    else:
        return None


def abbreviate(value):
    print(value.name)
    if value.name == "MATHEMATISCH-NATURWISSENSCHAFTLICHE KLASSE":
        return "math.-nat. Klasse"
    elif value.name == "PHILOSOPHISCH-HISTORISCHE KLASSE":
        return "phil.-hist. Klasse"
    else:
        return value


def get_date_range(rel, extended=False, original=False, format="%d.%m.%Y"):
    res = ""
    if extended:
        if rel.start_date_written is not None:
            res += f"von {rel.start_date_written if original else rel.start_date.strftime(format)}"
        if rel.end_date_written is not None:
            res += f" bis {rel.end_date_written if original else rel.end_date.strftime(format)}"
    else:
        if rel.start_date is not None:
            res += f"{rel.start_date.strftime('%Y')}"
        if rel.end_date_written is not None:
            res += f"-{rel.end_date.strftime('%Y')}"

    return res.strip()


berufslaufbahn_ids = get_child_classes([1851, 1385], PersonInstitutionRelation)

subs_akademie = get_child_institutions_from_parent([500, 2, 3])

promotion_inst_ids, promotion_inst_labels = get_child_classes(
    [1386], PersonInstitutionRelation, labels=True
)
daten_mappings = {1369: "Studium", 1371: "Studienaufenthalt", 1386: "Promotion"}

for i in promotion_inst_labels:
    daten_mappings[i[0]] = i[1].replace(">>", "in")


classes = {}
classes["vorschlag"] = get_child_classes(
    [3061, 3141], PersonPersonRelation, labels=True
)


def get_mitgliedschaft_from_relation(rel, abbreviate=True):
    lbl = rel.label.split(">>")[1].strip()
    if abbreviate:
        res = re.search(r"\((.+)\)", lbl)
        return res.group(1)
    else:
        return lbl


def get_gewaehlt(pers, year):
    rel = pers.personinstitution_set.filter(
        related_institution_id__in=[2, 3], start_date_written__contains=year
    ).order_by("start_date")
    if rel.count() == 0:
        return "nicht gewählt"
    date_vocs = ["Genehmigt", "Ernannt"]
    vocs = [
        f"{rel2.relation_type} am {rel2.start_date_written}"
        if rel2.relation_type.name in date_vocs
        else str(rel2.relation_type)
        for rel2 in rel
    ]
    return " und ".join(vocs)


def get_wahlvorschlag(pers):
    kls = (
        pers.personinstitution_set.filter(related_institution_id__in=[2, 3])
        .first()
        .related_institution
    )
    kls = abbreviate(kls)
    res = {}
    umwidm = [56, 57, 58, 59]
    for pp in pers.related_personB.filter(
        relation_type_id__in=classes["vorschlag"][0]
    ).order_by("start_date"):
        m = get_mitgliedschaft_from_relation(pp.relation_type)
        date = get_gewaehlt(pers, pp.start_date_written)
        txt = f"Zur Wahl zum {m} der {kls} {pp.start_date_written} vorgeschlagen von ({date}):"
        if (txt, pp.start_date) not in res.keys():
            res[(txt, pp.start_date)] = [
                pp.related_personA if pp.related_personA != pers else pp.related_personB
            ]
        else:
            res[(txt, pp.start_date)].append(
                pp.related_personA if pp.related_personA != pers else pp.related_personB
            )
    lst_fin = [(key[1], (key[0], value)) for key, value in res.items()]
    for pp in pers.personinstitution_set.filter(relation_type_id__in=umwidm):
        if "umgewidmet" in pp.relation_type.name.lower():
            lst_fin.append(
                (
                    pp.start_date,
                    f"Umgewidmet zum {get_mitgliedschaft_from_relation(pp.relation_type)} der {kls} {'am' if len(pp.start_date_written) > 4 else ''} {pp.start_date_written}",
                )
            )
    lst_fin_sort = sorted(lst_fin, key=lambda tup: tup[0])

    return lst_fin_sort


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
    normdaten_oebl = person_object.uri_set.filter(uri__contains="apis.acdh.oeaw")
    if normdaten_oebl.count() == 1:
        context["normdaten"].append(
            {
                "kind": "ÖBL",
                "uri": normdaten_oebl[0].uri,
                "identifier": normdaten_oebl[0].uri.split("/")[-1],
            }
        )
    normdaten_wgw = person_object.uri_set.filter(
        uri__contains="geschichtewiki.wien.gv.at"
    )
    if normdaten_wgw.count() == 1:
        context["normdaten"].append(
            {
                "kind": "WGW",
                "uri": normdaten_wgw[0].uri,
                "identifier": normdaten_wgw[0].uri.split("/")[-1],
            }
        )
    normdaten_gnd = person_object.uri_set.filter(uri__contains="d-nb.info")
    if normdaten_gnd.count() == 1:
        context["normdaten"].append(
            {
                "kind": "GND",
                "uri": normdaten_gnd[0].uri,
                "identifier": normdaten_gnd[0].uri.split("/")[-1],
            }
        )
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
            38,
            40,
            42,
            43,
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
            3459,
            3460,
            3471,
            129,
            130,
            131,
        ],
    ).order_by("start_date"):
        context["mitgliedschaften"].append(
            f"<span title='{rel.relation_type.label.split(' >> ')[1]} in der {rel.related_institution}'>{rel.relation_type.label.split(' >> ')[1].split('(')[0].strip()}</span> {rel.start_date.strftime('%Y')}{'-'+rel.end_date.strftime('%Y') if rel.end_date_written else ''}"
        )
    eltern = [
        p.related_personA
        for p in person_object.related_personA.filter(relation_type_id=168)
    ] + [
        p.related_personB
        for p in person_object.related_personB.filter(relation_type_id=169)
    ]
    eltern = [Person.objects.get(pk=p1) for p1 in eltern]
    eltern = [f"<a href=/person/{p.pk}>{str(p)}</a>" for p in eltern]
    kinder = [
        p.related_personA
        for p in person_object.related_personA.filter(relation_type_id=169)
    ] + [
        p.related_personB
        for p in person_object.related_personB.filter(relation_type_id=168)
    ]
    kinder = [Person.objects.get(pk=p1) for p1 in kinder]
    kinder = [f"<a href=/person/{p.pk}>{str(p)}</a>" for p in kinder]

    context["daten_akademie"] = {
        "schulbildung": [
            f'<a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>{", Abschluß " + rel.start_date.strftime("%Y") if rel.start_date is not None else ""}'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[176]
            )
        ],
        "studium": [
            f'<a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>{", " + daten_mappings[rel.relation_type_id] if rel.relation_type_id in daten_mappings.keys() else ""} {rel.start_date_written if rel.start_date_written and rel.relation_type_id in daten_mappings.keys() else ""}'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[1369, 1371] + promotion_inst_ids
            )
        ],
        "berufslaufbahn": [
            f'{rel.relation_type.label}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> ({rel.start_date_written if rel.start_date_written is not None else "ka"})'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=berufslaufbahn_ids
            ).exclude(related_institution_id__in=subs_akademie)
        ],
        "mitglied_in_einer_nationalsozialistischen_vereinigung": [
            f'Anwärter{"in" if person_object.gender == "female" else ""} der {rel.related_institution} {get_date_range(rel, extended=True)}'
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[3470, 3462]
            )
        ]
        + [
            f"Mitglied der {rel.related_institution} {get_date_range(rel, extended=True)}"
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[3452, 3451]
            )
        ]
        + [
            f"förderndes Mitglied der {rel.related_institution} {get_date_range(rel, extended=True)}"
            for rel in person_object.personinstitution_set.filter(
                relation_type_id__in=[3473]
            )
        ],
        "wahl_mitgliederstatus": [
            t[1][0]
            + " "
            + ", ".join(
                [
                    f'<a href="/person/{p2.pk}">{p2.first_name} {p2.name}</a>'
                    for p2 in t[1][1]
                ]
            )
            if isinstance(t[1], tuple)
            else t[1]
            for t in get_wahlvorschlag(person_object)
        ],
        "funktionen_in_der_akademie": [
            f'Zum Präsidenten der Gesamtakademie {rel.relation_type.name} am {rel.start_date_written}{", tätig bis "+rel.end_date_written if rel.end_date_written is not None else ""}'
            for rel in person_object.personinstitution_set.filter(
                related_institution_id=500, relation_type_id__in=[103, 106]
            )
        ]
        + [
            f'Zum Vizepräsidenten der Gesamtakademie {rel.relation_type.name} am {rel.start_date_written}{", tätig bis "+rel.end_date_written if rel.end_date_written is not None else ""}'
            for rel in person_object.personinstitution_set.filter(
                related_institution_id=500, relation_type_id__in=[107, 105]
            )
        ]
        + [
            f'Zum Sekretär der {abbreviate(rel.related_institution)} {rel.relation_type.name} am {rel.start_date_written}{", tätig bis "+rel.end_date_written if rel.end_date_written is not None else ""}'
            for rel in person_object.personinstitution_set.filter(
                related_institution_id__in=[2, 3], relation_type_id__in=[119, 118]
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
    if len(eltern) > 0 or len(kinder) > 0:
        context["daten_akademie"]["herkunft"] = []
        if len(eltern) > 0:
            context["daten_akademie"]["herkunft"].append(
                f"<b>Eltern</>: {', '.join(eltern)}"
            )
        if len(kinder) > 0:
            context["daten_akademie"]["herkunft"].append(
                f"<b>Kinder</>: {', '.join(kinder)}"
            )
    if person_object.personevent_set.filter(relation_type_id=3454).count() > 0:
        context["daten_akademie"][
            "mitglied_in_einer_nationalsozialistischen_vereinigung"
        ].append("Registrierungspflicht aufgrund des Verbotsgesetzes vom 1.5.1945")
    if person_object.personinstitution_set.filter(relation_type_id=26).count() > 0:
        lst_kom = [
            (rel.related_institution, get_date_range(rel))
            for rel in person_object.personinstitution_set.filter(relation_type_id=26)
        ]
        lst_kom = [
            f'<a href="/institution/{inst[0].pk}">{inst[0].name}</a> ({inst[1]})'
            for inst in lst_kom
        ]
        context["daten_akademie"]["funktionen_in_der_akademie"].append(
            f'Mitglied der folgenden Kommission{"en" if len(lst_kom) > 1 else ""}: {", ".join(lst_kom)}'
        )

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
