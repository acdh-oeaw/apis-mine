from datetime import date, timedelta
import glob
import re
import pickle
import os
from collections import OrderedDict

from django.conf import settings
from django.db.models import Q

from apis_core.apis_entities.models import Person, Institution, Event
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Collection
from apis_core.apis_relations.models import (
    PersonPlace,
    PersonPerson,
    PersonInstitution,
    InstitutionInstitution,
    InstitutionEvent,
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
    elif value.name == "Nationalsozialistische Deutsche Arbeiterpartei":
        return "NSDAP"
    elif value.name == "Nationalsozialistisches Fliegerkorps (NSFK)":
        return "NSFK"
    elif value.name == "Nationalsozialistische Volkswohlfahrt":
        return "NSV"
    else:
        return value


def get_date_range(
    rel, time_range_ids, extended=False, original=False, format="%d.%m.%Y"
):
    res = ""
    start = False
    end = False
    if rel.start_date_written:
        if len(rel.start_date_written) == 4 and extended:
            extended = False
    else:
        extended = False
    time_span = False
    if extended:
        if rel.start_date_written is not None:
            start = f"{rel.start_date_written if original else rel.start_date.strftime(format)}"
        if rel.end_date_written is not None:
            end = (
                f"{rel.end_date_written if original else rel.end_date.strftime(format)}"
            )
    else:
        if rel.start_date is not None:
            start = f"{rel.start_date.strftime('%Y')}"
        if rel.end_date is not None:
            end = f"{rel.end_date.strftime('%Y')}"
    if rel.relation_type_id in time_range_ids:
        res += "("
        if start:
            res += f"ab {start}"
        if end:
            res += f" bis {end})"
    elif start:
        res += f"({start})"
    if len(res.strip()) < 4:
        return ""
    res = res.replace("( ", "(").replace(" )", ")")
    return res.strip()


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


def get_academy_awards(award_type_id=137, rel_id=139, subs_akademie=None):
    res = []
    awards = Institution.objects.filter(kind_id=award_type_id).values_list(
        "pk", flat=True
    )
    for instinst in InstitutionInstitution.objects.filter(
        related_institutionA_id__in=awards,
        related_institutionB_id__in=subs_akademie,
        relation_type=rel_id,
    ):
        if instinst.related_institutionA_id not in res:
            res.append(instinst.related_institutionA_id)
    return res


def get_academy_preisaufgaben(
    preisaufgabe_type_id=123,
    rel_id=142,
    subs_akademie=None,
):
    res = []
    preisaufgaben = Event.objects.filter(kind_id=preisaufgabe_type_id).values_list(
        "pk", flat=True
    )
    for instevent in InstitutionEvent.objects.filter(
        related_event_id__in=preisaufgaben,
        related_institution_id__in=subs_akademie,
        relation_type=rel_id,
    ):
        if instevent.related_event_id not in res:
            res.append(instevent.related_event_id)
    return res


def create_data_utils(cache_path="cache/data_cache.pkl"):
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as inp:
            res = pickle.load(inp)
            return res

    berufslaufbahn_ids = get_child_classes([1851, 1385], PersonInstitutionRelation)
    subs_akademie = get_child_institutions_from_parent([500, 2, 3])
    promotion_inst_ids, promotion_inst_labels = get_child_classes(
        [1386], PersonInstitutionRelation, labels=True
    )
    daten_mappings = {1369: "Studium", 1371: "Studienaufenthalt", 1386: "Promotion"}

    for i in promotion_inst_labels:
        daten_mappings[i[0]] = i[1].replace(">>", "in")

    classes = {}
    classes["time_ranges_ids"] = [
        19,
        26,
        30,
        88,
        89,
        90,
        91,
        92,
        93,
        94,
        95,
        96,
        97,
        102,
        104,
        112,
        117,
        135,
        136,
        162,
        164,
        1369,
        1371,
        1376,
        3260,
        3488,
        4178,
    ]
    classes["time_ranges_ids"].extend(
        [
            x
            for x in get_child_classes([1851], PersonInstitutionRelation)
            if x not in classes["time_ranges_ids"]
        ]
    )
    classes["habilitation"] = get_child_classes([1385], PersonInstitutionRelation)
    classes["berufslaufbahn_ids"] = berufslaufbahn_ids
    classes["subs_akademie"] = subs_akademie
    classes["promotion_inst_ids"] = promotion_inst_ids
    classes["daten_mappings"] = daten_mappings
    classes["vorschlag"] = get_child_classes(
        [3061, 3141], PersonPersonRelation, labels=True
    )
    classes["mitgliedschaft"] = get_child_classes(
        [19, 20, 21, 23, 24], PersonInstitutionRelation, labels=True
    )
    classes["akad_funktionen"] = {
        "präsidentin": get_child_classes(
            [102, 1876], PersonInstitutionRelation, labels=True
        ),
        "vizepräsidentin": get_child_classes(
            [104], PersonInstitutionRelation, labels=True
        ),
        "generalsekretärin": get_child_classes(
            [112], PersonInstitutionRelation, labels=True
        ),
        "sekretärin": get_child_classes([117], PersonInstitutionRelation, labels=True),
        "obfrau/obmann": get_child_classes(
            [30], PersonInstitutionRelation, labels=True
        ),
        "mitglied kommission": get_child_classes(
            [26], PersonInstitutionRelation, labels=True
        ),
        "direktorin institut": get_child_classes(
            [3488, 88], PersonInstitutionRelation, labels=True
        ),
        "kuratorium": get_child_classes(
            [94, 95], PersonInstitutionRelation, labels=True
        ),
    }
    classes["akademiepreise"] = get_academy_awards(
        subs_akademie=classes["subs_akademie"] + [2, 3, 500]
    )
    classes["preisaufgaben"] = get_academy_preisaufgaben(
        subs_akademie=classes["subs_akademie"] + [2, 3, 500]
    )
    classes["berufslaufbahn_map"] = {
        "Professor/in": get_child_classes(
            [3534, 3404, 179, 180, 181, 182, 183],
            PersonInstitutionRelation,
            labels=False,
        ),
        "o. Professor/in": get_child_classes(
            [179], PersonInstitutionRelation, labels=False
        ),
        "ao. Professor/in": get_child_classes(
            [180], PersonInstitutionRelation, labels=False
        ),
        "Rektor/in": [1874],
        "Dekan/in": [1873],
        "Mitarbeiter/in": get_child_classes(
            [4099, 3530, 3381, 3350], PersonInstitutionRelation, labels=False
        ),
        "leitende Mitarbeiter/in": get_child_classes(
            [3488, 3479, 3423, 3422, 3177, 3077, 1872, 1871],
            PersonInstitutionRelation,
            labels=False,
        ),
    }

    with open(cache_path, "wb") as outp:
        pickle.dump(classes, outp)
    return classes


classes = create_data_utils()


def get_wahlvorschlag(pers):
    kls = (
        pers.personinstitution_set.filter(related_institution_id__in=[2, 3])
        .first()
        .related_institution
    )
    kls = abbreviate(kls)
    res = {}
    umwidm = [56, 57, 58, 59]
    ruhend = [3457, 3456, 3374, 3373]
    reaktiviert = [3471, 3460, 3459]
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
    for pp in pers.personinstitution_set.filter(relation_type_id__in=ruhend):
        if "ruhend gestellt" in pp.relation_type.name.lower():
            lst_fin.append(
                (
                    pp.start_date,
                    f"Ruhend gestellt als {get_mitgliedschaft_from_relation(pp.relation_type)} der {kls} {'am' if len(pp.start_date_written) > 4 else ''} {pp.start_date_written}",
                )
            )
    for pp in pers.personinstitution_set.filter(relation_type_id__in=reaktiviert):
        if "reaktiviert" in pp.relation_type.name.lower():
            lst_fin.append(
                (
                    pp.start_date,
                    f"Reaktiviert als {get_mitgliedschaft_from_relation(pp.relation_type)} der {kls} {'am' if len(pp.start_date_written) > 4 else ''} {pp.start_date_written}",
                )
            )
    lst_fin_sort = sorted(lst_fin, key=lambda tup: tup[0])

    return lst_fin_sort


def create_text_berufslaufbahn(rel):
    lst_rels = rel.relation_type.label.split(">>")
    if rel.relation_type_id in classes["berufslaufbahn_map"]["Professor/in"]:
        return f"{lst_rels[1]} für {lst_rels[2]}"
    elif rel.relation_type_id in classes["habilitation"]:
        return f"Habilitation in {lst_rels[1]}"
    elif rel.relation_type_id == 3088:
        return "Ehrendoktorat von"
    else:
        return lst_rels[-1]


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

    context["daten_akademie"] = OrderedDict(
        {
            "Schulbildung": [
                f'<a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>{", Abschluß " + rel.start_date.strftime("%Y") if rel.start_date is not None else ""}'
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=[176]
                )
            ],
            "Studium": [
                f'<a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>{", " + classes["daten_mappings"][rel.relation_type_id] if rel.relation_type_id in classes["daten_mappings"].keys() else ""} {rel.start_date_written if rel.start_date_written and rel.relation_type_id in classes["daten_mappings"].keys() else ""}'
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=[1369, 1371] + classes["promotion_inst_ids"]
                )
            ],
            "Berufslaufbahn": [
                f'{create_text_berufslaufbahn(rel)}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a> {get_date_range(rel, classes["time_ranges_ids"], extended=True)}'
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=classes["berufslaufbahn_ids"]
                ).exclude(
                    related_institution_id__in=classes["subs_akademie"] + [2, 3, 500]
                )
            ],
            "Mitglied in einer nationalsozialistischen Vereinigung": [
                f'Anwärter{"in" if person_object.gender == "female" else ""} der {rel.related_institution} {get_date_range(rel, classes["time_ranges_ids"], extended=True)}'
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=[3470, 3462]
                )
            ]
            + [
                f"Mitglied der <span data-toggle='tooltip' title='{rel.related_institution}'>{abbreviate(rel.related_institution)}</span> {get_date_range(rel, classes['time_ranges_ids'], extended=True)}"
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=[3452, 3451]
                )
            ]
            + [
                f"förderndes Mitglied der <span data-toggle='tooltip' title='{rel.related_institution}'>{abbreviate(rel.related_institution)}</span> {get_date_range(rel, classes['time_ranges_ids'], extended=True)}"
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=[3473]
                )
            ],
            "Wahl und Mitgliedschaft": [
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
            "Funktionen in der Akademie": [
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
    )
    if len(eltern) > 0 or len(kinder) > 0:
        context["daten_akademie"]["Eltern und Kinder"] = []
        if len(eltern) > 0:
            context["daten_akademie"]["Eltern und Kinder"].append(
                f"<span>Eltern</>:<br/> {', '.join(eltern)}"
            )
        if len(kinder) > 0:
            context["daten_akademie"]["Eltern und Kinder"].append(
                f"<span>Kinder</>: {', '.join(kinder)}"
            )
        context["daten_akademie"].move_to_end("Eltern und Kinder", last=False)
    if person_object.personevent_set.filter(relation_type_id=3454).count() > 0:
        context["daten_akademie"][
            "Mitglied in einer nationalsozialistischen Vereinigung"
        ].append("Registrierungspflicht aufgrund des Verbotsgesetzes vom 1.5.1945")
    if person_object.personinstitution_set.filter(relation_type_id=26).count() > 0:
        lst_kom = dict()
        for rel in person_object.personinstitution_set.filter(
            relation_type_id=26
        ).order_by("start_date"):
            if rel.related_institution not in lst_kom.keys():
                lst_kom[rel.related_institution] = [
                    get_date_range(rel, classes["time_ranges_ids"])[1:-1]
                ]
            else:
                lst_kom[rel.related_institution].append(
                    get_date_range(rel, classes["time_ranges_ids"])[1:-1]
                )
        lst_kom = [
            f'<a href="/institution/{inst.pk}">{inst.name}</a> ({", ".join(dates)})'
            for inst, dates in lst_kom.items()
        ]
        context["daten_akademie"]["Funktionen in der Akademie"].append(
            f'Mitglied der folgenden Kommission{"en" if len(lst_kom) > 1 else ""}: {", ".join(lst_kom)}'
        )
    if (
        "Mitglied in einer nationalsozialistischen Vereinigung"
        in context["daten_akademie"].keys()
    ):
        context["daten_akademie"].move_to_end(
            "Mitglied in einer nationalsozialistischen Vereinigung"
        )

    return context


col_oebl = getattr(settings, "APIS_OEBL_BIO_COLLECTION", "ÖBL Biographie")
col_oebl = Collection.objects.filter(name=col_oebl)
if col_oebl.count() == 1:
    oebl_persons = Person.objects.filter(collection=col_oebl[0])
else:
    oebl_persons = Person.objects.all()


person_place_born = PersonPlace.objects.filter(
    relation_type__name__icontains=getattr(settings, "BIRTH_REL_NAME", "birth")
)
person_place_death = PersonPlace.objects.filter(
    relation_type__name__icontains=getattr(settings, "DEATH_REL_NAME", "death")
)


oebl_persons_with_date = oebl_persons.exclude(Q(start_date=None) | Q(end_date=None))


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