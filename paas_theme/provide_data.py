from datetime import date, timedelta, datetime
import glob
import re
import pickle
import os
from collections import OrderedDict
import copy

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
    LabelType,
    PersonPersonRelation,
    PersonEventRelation,
    PersonInstitutionRelation,
    PersonPlaceRelation,
    PersonWorkRelation,
)

from paas_theme import id_mapping


from .helper_functions import abbreviate, get_mitgliedschaft_from_relation

MITGLIEDER = Person.objects.filter(
    collection__name=getattr(id_mapping, "MITGLIED_AUSWERTUNG_COL_NAME")
)
MITGLIDER_NS = Person.objects.filter(
    collection__name=getattr(id_mapping, "MITGLIED_AUSWERTUNG_NS_COL_NAME")
)
NATIONALSOZIALISTEN = Person.objects.filter(
    collection__name=getattr(id_mapping, "NATIONALSOZIALISTEN_COL_NAME")
)
KOMMISSIONEN = Institution.objects.filter(
    kind__id=getattr(id_mapping, "AKADEMIE_KOMMISSION_TYP_ID")
).exclude(name="GEMEINSAME KOMMISSIONEN")

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


def get_child_institutions_from_parent(insts, vocab_id=2):
    res = []
    insts_copy = copy.deepcopy(insts)
    i = insts_copy.pop()
    while i:
        for ii in InstitutionInstitution.objects.filter(
            related_institutionB_id=i, relation_type_id=vocab_id
        ):
            if ii.related_institutionA_id not in res:
                res.append(ii.related_institutionA_id)
                if ii.related_institutionA_id not in insts_copy:
                    insts_copy.append(ii.related_institutionA_id)
        if len(insts_copy) > 0:
            i = insts_copy.pop()
        else:
            i = False

    return res


def get_main_text(MAIN_TEXT):
    if MAIN_TEXT is not None:
        return MAIN_TEXT
    else:
        return None


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
        if start and end:
            res += f"{start}-{end})"
        else:
            if start:
                res += f"ab {start}"
            if end:
                res += f" bis {end})"
            else:
                res += ")"
    elif start:
        res += f"({start})"
    if len(res.strip()) < 4:
        return ""
    res = res.replace("( ", "(").replace(" )", ")")
    return res.strip()


def get_gewaehlt(pers, year):
    rel = pers.personinstitution_set.filter(
        related_institution_id__in=getattr(id_mapping, "KLASSEN_IDS"),
        start_date_written__contains=year,
    ).order_by("start_date")
    if rel.count() == 0:
        return "nicht gewählt", None
    date_vocs = [
        "Genehmigt",
        "Ernannt",
        "gewählt und bestätigt",
        "gewählt und genehmigt",
        "gewählt und ernannt",
        "gewählt",
    ]
    vocs = [
        f"{rel2.relation_type} am {rel2.start_date_written}"
        if rel2.relation_type.name in date_vocs
        else str(rel2.relation_type)
        for rel2 in rel
    ]
    functions = [get_mitgliedschaft_from_relation(r.relation_type) for r in rel]
    return " und ".join(vocs), functions


def get_academy_awards(
    award_type_id=137,
    rel_id=[139, 2],
    subs_akademie=getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN"),
):
    res = []
    awards = Institution.objects.filter(kind_id=award_type_id).values_list(
        "pk", flat=True
    )
    for instinst in InstitutionInstitution.objects.filter(
        related_institutionA_id__in=list(awards),
        related_institutionB_id__in=list(subs_akademie),
        relation_type_id__in=rel_id,
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
    subs_akademie = get_child_institutions_from_parent(
        getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")
    )
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
        3470,
        3462,
        3452,
        3451,
        3473,
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
    classes["image_wiki"] = LabelType.objects.get(name="Wikicommons Image").pk
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
    classes["mitgliedschaft sortiert"] = ["wM", "kM I", "kM A", "EM"]
    classes["ausschluss"] = [4170, 4171, 3458, 3464, 3474]
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
        subs_akademie=classes["subs_akademie"]
        + getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")
    )
    classes["preisaufgaben"] = get_academy_preisaufgaben(
        subs_akademie=classes["subs_akademie"]
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
    classes["netzwerk"] = {
        "Kommissionen": {
            "relation": "PersonInstitution",
            "related_institution__kind_id": getattr(
                id_mapping, "AKADEMIE_KOMMISSION_TYP_ID"
            ),
            "relation_type_id__in": get_child_classes(
                [26, 162], PersonInstitutionRelation, labels=False
            ),
        },
        "Universitäten": {
            "relation": "PersonInstitution",
            "label": "Prof. an Universitäten",
            "related_institution__kind_id": 3383,
            "relation_type_id__in": classes["berufslaufbahn_map"]["Professor/in"],
        },
        "Orte": {
            "relation": "PersonPlace",
            "label": "Geburts- und Sterbeorte",
            "relation_type_id__in": [64, 3090, 152, 153, 3054, 3091],
        },
    }
    classes["linked_search_institution"] = {
        "kommission": {
            "label": "Kommissionen",
            "qs": {
                "related_institution__kind_id": getattr(
                    id_mapping, "AKADEMIE_KOMMISSION_TYP_ID"
                ),
                "relation_type_id__in": [
                    164,  # Kooptiertes Mitglied
                    162,  # StellvertreterIn
                    30,  # Obfrau/Obmann
                    26,  # Mitglied
                ],
            },
        }
    }
    classes["inst_typ"] = {
        "Kommission": [getattr(id_mapping, "AKADEMIE_KOMMISSION_TYP_ID")],
        "Institut": [83],
        "Forschungsstelle": [84],
    }
    with open(cache_path, "wb") as outp:
        pickle.dump(classes, outp)
    return classes


classes = create_data_utils()


def get_wahlvorschlag(pers, mitgliedschaften):
    rel_inst_1 = pers.personinstitution_set.filter(
        related_institution_id__in=getattr(id_mapping, "KLASSEN_IDS")
    )
    if rel_inst_1.count() > 0:
        kls = rel_inst_1.first().related_institution
        kls = abbreviate(kls)
    else:
        kls = ""
    res = {}
    umwidm = [56, 57, 58, 59]
    ruhend = getattr(id_mapping, "RUHEND_GESTELLT")
    reaktiviert = [3471, 3460, 3459]
    lst_gew = []
    for pp in (
        pers.related_personB.filter(relation_type_id__in=classes["vorschlag"][0])
        .exclude(start_date_written__isnull=True)
        .order_by("start_date")
    ):
        m = get_mitgliedschaft_from_relation(pp.relation_type)
        date, funk = get_gewaehlt(pers, pp.start_date_written)
        txt = f"{pp.start_date_written} zur Wahl zum {m} der {kls} vorgeschlagen von:"
        if (txt, pp.start_date) not in res.keys():
            res[(txt, pp.start_date)] = [
                pp.related_personA if pp.related_personA != pers else pp.related_personB
            ]
        else:
            res[(txt, pp.start_date)].append(
                pp.related_personA if pp.related_personA != pers else pp.related_personB
            )
        if date:
            if funk is not None:
                txt_1 = f"als {', '.join(funk)} {date[0].lower()+date[1:]}"
            else:
                txt_1 = date
            if (pp.start_date, txt_1) not in lst_gew:
                lst_gew.append((pp.start_date, txt_1))
                lst_gew.append((pp.start_date, "<hr/>"))
    lst_fin = [(key[1], (key[0], value)) for key, value in res.items()]
    if len(lst_gew) > 0:
        lst_fin += lst_gew
    for pp in pers.personinstitution_set.filter(relation_type_id__in=umwidm):
        if "umgewidmet" in pp.relation_type.name.lower():
            lst_fin.append(
                (
                    pp.start_date,
                    f"{'am' if len(pp.start_date_written) > 4 else ''} {pp.start_date_written} umgewidmet zum {get_mitgliedschaft_from_relation(pp.relation_type)} der {kls}",
                )
            )
            lst_fin.append((pp.start_date, "<hr/>"))
    for pp in pers.personinstitution_set.filter(relation_type_id__in=ruhend):
        if "ruhend gestellt" in pp.relation_type.name.lower():
            lst_fin.append(
                (
                    pp.start_date,
                    f"{'am' if len(pp.start_date_written) > 4 else ''} {pp.start_date_written} ruhend gestellt als {get_mitgliedschaft_from_relation(pp.relation_type)} der {kls}",
                )
            )
            lst_fin.append((pp.start_date, "<hr/>"))
    for pp in pers.personinstitution_set.filter(relation_type_id__in=reaktiviert):
        if "reaktiviert" in pp.relation_type.name.lower():
            lst_fin.append(
                (
                    pp.start_date,
                    f"{'am' if len(pp.start_date_written) > 4 else ''} {pp.start_date_written} reaktiviert als {get_mitgliedschaft_from_relation(pp.relation_type)} der {kls}",
                )
            )
            lst_fin.append((pp.start_date, "<hr/>"))
    for mit in mitgliedschaften:
        if (
            mit[0]
            not in [
                x[0] if isinstance(x[0], str) else x[0].strftime("%Y") for x in lst_fin
            ]
            and mit[-1]
            and mit[5].relation_type_id in classes["ausschluss"]
        ):
            lst_fin.append(
                (
                    datetime.strptime(mit[0], "%Y").date(),
                    f"{mit[0]} {mit[2]}",
                )
            )
            lst_fin.append((datetime.strptime(mit[0], "%Y").date(), "<hr/>"))
        elif (
            mit[0]
            not in [
                x[0] if isinstance(x[0], str) else x[0].strftime("%Y") for x in lst_fin
            ]
            and mit[-1]
        ):
            lst_fin.append(
                (
                    datetime.strptime(mit[0], "%Y").date(),
                    f"{mit[0]} zum {mit[2]} der {abbreviate(mit[4])} {mit[-1].lower()}",
                )
            )
            lst_fin.append((datetime.strptime(mit[0], "%Y").date(), "<hr/>"))
    lst_fin_sort = sorted(lst_fin, key=lambda tup: tup[0])

    return lst_fin_sort[:-1]


def create_text_berufslaufbahn(rel):
    lst_rels = rel.relation_type.label.split(">>")

    if rel.relation_type_id in classes["berufslaufbahn_map"]["Professor/in"]:
        try:
            return f"{lst_rels[1]} für {lst_rels[2]}"
        except IndexError:
            return lst_rels[1]
    elif rel.relation_type_id in classes["habilitation"]:
        try:
            return f"Habilitation in {lst_rels[1]}"
        except IndexError:
            return "Habilitation"
    elif rel.relation_type_id == 3088:
        return "Ehrendoktorat von"
    else:
        return lst_rels[-1]


def get_references_tooltip(rel):
    if len(rel.references) > 0:
        res = f"<span class='tooltip-mine ml-1'>R<span class='tooltiptext'>{rel.references}</span></span>"
        return res
    else:
        return ""


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
                "identifier": normdaten_wgw[0].uri.split("=")[-1],
            }
        )
    normdaten_gnd = person_object.uri_set.filter(uri__contains="d-nb.info")
    if normdaten_gnd.count() == 1:
        gnd_identifier = normdaten_gnd[0].uri.split("/")[-1]
        context["normdaten"].append(
            {
                "kind": "GND",
                "uri": f"https://portal.dnb.de/opac/simpleSearch?reset=true&cqlMode=true&query=auRef%3D{gnd_identifier}&selectedCategory=any",
                "identifier": gnd_identifier,
            }
        )
    normdaten_wikidata = person_object.uri_set.filter(uri__contains="wikidata")
    if normdaten_wikidata.count() == 1:
        context["normdaten"].append(
            {
                "kind": "Wikidata",
                "uri": normdaten_wikidata[0].uri,
                "identifier": normdaten_wikidata[0].uri.split("/")[-1],
            }
        )
    normdaten_db = person_object.uri_set.filter(uri__contains="deutsche-biographie")
    if normdaten_db.count() == 1:
        context["normdaten"].append(
            {
                "kind": "Deutsche Biographie",
                "uri": normdaten_db[0].uri,
                "identifier": normdaten_db[0].uri.split("/")[-1].split(".")[0],
            }
        )
    normdaten_parlament = person_object.uri_set.filter(uri__contains="parlament")
    if normdaten_parlament.count() == 1:
        context["normdaten"].append(
            {
                "kind": "Österreichisches Parlament",
                "uri": normdaten_parlament[0].uri,
                "identifier": normdaten_parlament[0].uri.split("_")[-1][:-1],
            }
        )
    img_fn = person_object.label_set.filter(label_type__name="filename OEAW Archiv")
    if img_fn.count() == 1:
        img_fn = img_fn.first().label
        lst_images = glob.glob(
            f"{getattr(settings, 'APIS_PAAS_IMAGE_FOLDER')}/{img_fn}"
        )
    else:
        lst_images = []
    if len(lst_images) == 1:
        fig_caption = person_object.label_set.filter(
            label_type__name=getattr(
                settings, "APIS_PAAS_FIGURE_CAPTION", "photocredit OEAW Archiv"
            )
        )
        if fig_caption.count() == 1:
            fig_caption = fig_caption.first().label
        else:
            fig_caption = "OEAW"
        context["image"] = (True, lst_images[0].split("/")[-1], fig_caption)
    elif classes.get("image_wiki", False):
        if (
            person_object.label_set.filter(
                label_type_id=classes.get("image_wiki")
            ).count()
            > 0
        ):
            context["image"] = (
                False,
                (
                    person_object.label_set.filter(label_type_id=classes["image_wiki"])
                    .first()
                    .label
                ),
            )
    else:
        context["image"] = False
    preise = []
    for nobel in person_object.personinstitution_set.filter(
        relation_type_id=138,
        related_institution_id__in=getattr(id_mapping, "NOBEL_PREISE"),
    ):
        preise.append(
            f"{nobel.related_institution.name}, {get_date_range(nobel, classes['time_ranges_ids'])[1:-1]}"
        )
    for ewk in person_object.personinstitution_set.filter(
        relation_type_id=138, related_institution_id=29953
    ):
        preise.append(
            f"{ewk.related_institution.name}{', '+get_date_range(ewk, classes['time_ranges_ids'])[1:-1] if len(get_date_range(ewk, classes['time_ranges_ids'])) > 0 else ''}"
        )
    akad_preise = ""
    for akadp in person_object.personinstitution_set.filter(
        related_institution_id__in=classes["akademiepreise"], relation_type_id=138
    ).exclude(relation_type_id=3501):
        akad_preise += f"<li><a href='/institution/{akadp.related_institution_id}'>{akadp.related_institution}</a>{' '+get_date_range(akadp, classes['time_ranges_ids'])[1:-1] if len(get_date_range(akadp, classes['time_ranges_ids'])) > 0 else ''}</li>"
    if len(akad_preise) > 0:
        akad_preise = (
            "Ausgezeichnet mit folgenden Akademiepreisen:<ul>" + akad_preise + "</ul>"
        )
        preise.append(akad_preise)
    preis_auf = ""
    for preisauf in person_object.personevent_set.filter(
        related_event_id__in=classes["preisaufgaben"], relation_type_id=143
    ):
        preis_auf += f"<li><a href='/event/{preisauf.related_event_id}'>{preisauf.related_event}</a></li>"
    if len(preis_auf) > 0:
        akad_preisauf = "Gewann folgende Preisaufgaben:<ul>" + preis_auf + "</ul>"
        preise.append(akad_preisauf)
    context["mitgliedschaften"] = []
    rel_test = []
    mitgliedschaften = []
    for rel in person_object.personinstitution_set.filter(
        related_institution_id__in=getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN"),
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
            3457,
            3456,
            3374,
            3373,
            4176,
            4177,
            4174,
            4180,
            4179,
            129,
            130,
            131,
        ]
        + classes["ausschluss"],
    ).order_by("start_date"):
        mitgliedschaften.append(
            (
                rel.start_date.strftime("%Y"),
                rel.end_date.strftime("%Y") if rel.end_date_written else None,
                rel.relation_type.label.split(" >> ")[1].split("(")[0].strip(),
                rel.relation_type.label.split(" >> ")[1],
                rel.related_institution,
                rel,
                rel.relation_type.label.split(" >> ")[-1],
            )
        )
        """         context["mitgliedschaften"].append(
            f"<span title='{rel.relation_type.label.split(' >> ')[1]} in der {rel.related_institution}'>{rel.relation_type.label.split(' >> ')[1].split('(')[0].strip()}</span> {rel.start_date.strftime('%Y')}{'-'+rel.end_date.strftime('%Y') if rel.end_date_written else ''}"
        ) """
    context["mitgliedschaften"] = []
    for mit in mitgliedschaften:
        if mit[5].relation_type_id in classes["ausschluss"]:
            context["mitgliedschaften"].append(f"{mit[0]} {mit[3]}")
        elif mit[6].lower() == "ruhend gestellt":
            context["mitgliedschaften"].append(
                f"{mit[0]} <span title='{mit[2]} in der {mit[4]}'>{mit[2]}</span> ({mit[6]})"
            )
        else:
            context["mitgliedschaften"].append(
                f"{mit[0]} <span title='{mit[2]} in der {mit[4]}'>{mit[2]}</span>"
            )
    eltern = [
        p.related_personA
        for p in person_object.related_personA.filter(relation_type_id=168)
    ] + [
        p.related_personB
        for p in person_object.related_personB.filter(relation_type_id=169)
    ]
    eltern = [Person.objects.get(pk=p1) for p1 in eltern]
    if len(eltern) > 0:
        eltern_dict = {"Vater": "k. A.", "Mutter": "k. A."}
        for p in eltern:
            if p.gender == "female":
                eltern_dict["Mutter"] = f"<a href=/person/{p.pk}>{str(p)}</a>"
            else:
                eltern_dict["Vater"] = f"<a href=/person/{p.pk}>{str(p)}</a>"
        eltern = [f"{key}: {value}" for key, value in eltern_dict.items()]
    """     kinder = [
        p.related_personA
        for p in person_object.related_personA.filter(relation_type_id=169)
    ] + [
        p.related_personB
        for p in person_object.related_personB.filter(relation_type_id=168)
    ] """
    # kinder = [Person.objects.get(pk=p1) for p1 in kinder]
    # kinder = [f"<a href=/person/{p.pk}>{str(p)}</a>" for p in kinder]

    context["daten_akademie"] = OrderedDict(
        {
            "Schulbildung": [
                f'<a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>{", Abschluß " + rel.start_date.strftime("%Y") if rel.start_date is not None else ""}'
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=[176]
                )
            ],
            "Studium": [
                f'<a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>{", " + classes["daten_mappings"][rel.relation_type_id] if rel.relation_type_id in classes["daten_mappings"].keys() else ""} {get_date_range(rel, classes["time_ranges_ids"], extended=True)}'
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=[1369, 1371] + classes["promotion_inst_ids"]
                )
            ],
            "Berufslaufbahn": [
                f'{create_text_berufslaufbahn(rel)}: <a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>{get_references_tooltip(rel)} {get_date_range(rel, classes["time_ranges_ids"], extended=True)}'
                for rel in person_object.personinstitution_set.filter(
                    relation_type_id__in=classes["berufslaufbahn_ids"]
                ).exclude(
                    related_institution_id__in=classes["subs_akademie"]
                    + getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")
                )
            ],
            "Mitglied in einer nationalsozialistischen Vereinigung": [
                f'Anwärter{"in" if person_object.gender == "female" else ""} folgender nationalsozialistischer Vereinigungen: <ul>'
                + "".join(
                    [
                        f'<li>{rel.related_institution} {get_date_range(rel, classes["time_ranges_ids"], extended=True)}</li>'
                        for rel in person_object.personinstitution_set.filter(
                            relation_type_id__in=[3470, 3462]
                        )
                    ]
                )
                + "</ul><hr/>"
                if person_object.personinstitution_set.filter(
                    relation_type_id__in=[3470, 3462]
                ).count()
                > 0
                else ""
            ]
            + [
                "Mitglied folgender nationalsozialistischer Vereinigungen: <ul>"
                + "".join(
                    [
                        f"<li>{rel.related_institution} {get_date_range(rel, classes['time_ranges_ids'], extended=True)}</li>"
                        for rel in person_object.personinstitution_set.filter(
                            relation_type_id__in=[3452, 3451]
                        )
                    ]
                )
                + "</ul><hr/>"
                if person_object.personinstitution_set.filter(
                    relation_type_id__in=[3452, 3451]
                ).count()
                > 0
                else ""
            ]
            + [
                f"förderndes Mitglied folgender nationalsozialistischer Vereinigungen: <ul>"
                + "".join(
                    [
                        f"<li><{rel.related_institution} {get_date_range(rel, classes['time_ranges_ids'], extended=True)}</li>"
                        for rel in person_object.personinstitution_set.filter(
                            relation_type_id__in=[3473]
                        )
                    ]
                )
                if person_object.personinstitution_set.filter(
                    relation_type_id__in=[3473]
                ).count()
                > 0
                else ""
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
                for t in get_wahlvorschlag(person_object, mitgliedschaften)
            ],
            "Funktionen in der Akademie": [
                f'Zum Präsidenten der Gesamtakademie {rel.relation_type.name} am {rel.start_date_written}{", tätig bis "+rel.end_date_written if rel.end_date_written is not None else ""}'
                for rel in person_object.personinstitution_set.filter(
                    related_institution_id=500,
                    relation_type_id__in=classes["akad_funktionen"]["präsidentin"][0],
                )
            ]
            + [
                f'Zum Vizepräsidenten der Gesamtakademie {rel.relation_type.name} am {rel.start_date_written}{", tätig bis "+rel.end_date_written if rel.end_date_written is not None else ""}'
                for rel in person_object.personinstitution_set.filter(
                    related_institution_id=500,
                    relation_type_id__in=classes["akad_funktionen"]["vizepräsidentin"][
                        0
                    ],
                )
            ]
            + [
                f'Zum Sekretär der {abbreviate(rel.related_institution)} {rel.relation_type.name} am {rel.start_date_written}{", tätig bis "+rel.end_date_written if rel.end_date_written is not None else ""}'
                for rel in person_object.personinstitution_set.filter(
                    related_institution_id__in=getattr(
                        id_mapping, "GESAMTAKADEMIE_UND_KLASSEN"
                    ),
                    relation_type_id__in=classes["akad_funktionen"]["sekretärin"][0],
                )
            ],
            "Mitgliedschaften in anderen Akademien": [
                f'<a href="/institution/{rel.related_institution_id}">{rel.related_institution}</a>, {rel.relation_type.name} {get_date_range(rel, classes["time_ranges_ids"])}'
                for rel in person_object.personinstitution_set.filter(
                    related_institution__kind_id=3378
                ).order_by("related_institution__name")
            ],
            "Auszeichnungen und Preisaufgaben": [
                f"{p}<hr/>" if idx < len(preise) - 1 else p
                for idx, p in enumerate(preise)
            ],
        }
    )
    if len(eltern) > 0:
        context["daten_akademie"]["Eltern"] = []
        context["daten_akademie"]["Eltern"].append(f" {'<br/>'.join(eltern)}")
        context["daten_akademie"].move_to_end("Eltern", last=False)
    if person_object.personevent_set.filter(relation_type_id=3454).count() > 0:
        context["daten_akademie"][
            "Mitglied in einer nationalsozialistischen Vereinigung"
        ].append("Registrierungspflicht aufgrund des Verbotsgesetzes vom 1.5.1945")
    test_ns = False
    for t in context["daten_akademie"][
        "Mitglied in einer nationalsozialistischen Vereinigung"
    ]:
        if len(t) > 0:
            test_ns = True
            break
    if not test_ns:
        del context["daten_akademie"][
            "Mitglied in einer nationalsozialistischen Vereinigung"
        ]

    speeches = person_object.personwork_set.filter(relation_type_id=4317).all()

    if speeches:

        list_speeches_html = [
            f'<li><a href="/work/{speech.related_work.pk}">"{speech.related_work.name}"</a> (<a href="/event/{speech.related_work.eventwork_set.first().related_event.pk}">{speech.related_work.eventwork_set.first().related_event.name}</a>, {speech.start_date.strftime("%d.%m.%Y")})</li>'
            for speech in speeches.order_by("start_date")
        ]

        context["daten_akademie"]["Rede in einer feierlichen Sitzung"] = [
            f'<ul class="list-unstyled pl-3">{"".join(list_speeches_html)}</ul>'
        ]

    # Obmannship...
    if (
        person_object.personinstitution_set.filter(relation_type_id__in=[30]).count()
        > 0
    ):

        lst_kom = dict()

        for rel in person_object.personinstitution_set.filter(
            relation_type_id__in=[30]
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
            f'<li><a href="/institution/{inst.pk}">{inst.name}</a> ({", ".join(dates)})</li>'
            for inst, dates in lst_kom.items()
        ]
        context["daten_akademie"]["Funktionen in der Akademie"].append(
            f'Obmann/Obfrau der folgenden Kommission{"en" if len(lst_kom) > 1 else ""}: <ul class="list-unstyled pl-3">{"".join(lst_kom)}</ul>'
        )
    # Membership...
    if (
        person_object.personinstitution_set.filter(relation_type_id__in=[26]).count()
        > 0
    ):

        lst_kom = dict()

        for rel in person_object.personinstitution_set.filter(
            relation_type_id__in=[26]
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
            f'<li><a href="/institution/{inst.pk}">{inst.name}</a> ({", ".join(dates)})</li>'
            for inst, dates in lst_kom.items()
        ]
        context["daten_akademie"]["Funktionen in der Akademie"].append(
            f'{"Mitglied der folgenden Kommissionen/Kuratorien" if len(lst_kom) > 1 else "Mitglied der folgenden Kommission/des folgenden Kuratoriums"} : <ul class="list-unstyled pl-3">{"".join(lst_kom)}</ul>'
        )

    if (
        "Mitglied in einer nationalsozialistischen Vereinigung"
        in context["daten_akademie"].keys()
    ):
        context["daten_akademie"].move_to_end(
            "Mitglied in einer nationalsozialistischen Vereinigung"
        )

    return context


def get_typ_of_institution(inst):
    for k, v in classes["inst_typ"].items():
        if inst.kind_id in v:
            return k


# def enrich_institution_context(institution_object, context):


def enrich_institution_context(institution_object, context):
    context["relatedinstitutions"] = get_child_institutions_from_parent(
        [institution_object.pk]
    )
    if institution_object.pk in classes["subs_akademie"] + getattr(
        id_mapping, "GESAMTAKADEMIE_UND_KLASSEN"
    ):
        context["akademie"] = True
    else:
        context["akademie"] = False
    context["typ"] = get_typ_of_institution(institution_object)
    rel_akad = institution_object.related_institutionB.filter(
        related_institutionB_id__in=getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")
    ).values_list("related_institutionB__name", flat=True)
    if rel_akad.count() > 0:
        context[
            "untertitel"
        ] = f"{context['typ']} der {rel_akad[0].replace('E KLASSE', 'EN KLASSE')}"
    else:
        loc = institution_object.institutionplace_set.filter(relation_type_id=159)
        if loc.count() == 1:
            loc = loc[0]
            if loc.related_place.lat:
                context["gelegen_in"] = (loc.related_place.lat, loc.related_place.lng)

    if context["typ"] == "Kommission":
        context["struktur"] = [
            f"<a href='/institution/{kom.pk}'>{kom.name}</a></br>{kom.start_date_written if kom.start_date_written else ''} - {kom.end_date_written if kom.end_date_written else ''}"
            for kom in Institution.objects.filter(
                pk__in=get_child_institutions_from_parent([institution_object])
            )
        ] + [
            f"<a href='/institution/{instinst.related_institutionA_id}'>{instinst.related_institutionA.name}</a></br>Eingegliedert in die {institution_object.name} {'am '+instinst.start_date.strftime('%d.%m.%Y') if instinst.start_date else ''}"
            for instinst in institution_object.related_institutionA.filter(
                relation_type_id=4203
            )
        ]

    context["daten_institution"] = {
        "OBFRAUEN / OBMÄNNER": [
            f"{pi.start_date.strftime('%Y') if pi.start_date else ''} - {pi.end_date.strftime('%Y') if pi.end_date else ''} <a href='/person/{pi.related_person_id}'>{pi.related_person.first_name} {pi.related_person.name}</a>"
            for pi in institution_object.personinstitution_set.filter(
                relation_type_id__in=classes["akad_funktionen"]["obfrau/obmann"][0]
            ).order_by("start_date")
        ],
        "KURATORIUM": [
            f"{pi.start_date.strftime('%Y') if pi.start_date else ''} - {pi.end_date.strftime('%Y') if pi.end_date else ''} <a href='/person/{pi.related_person_id}'>{pi.related_person.first_name} {pi.related_person.name}</a>"
            for pi in institution_object.personinstitution_set.filter(
                relation_type_id__in=classes["akad_funktionen"]["kuratorium"][0]
            ).order_by("start_date")
        ],
        "INSTITUTIONELLE VORLÄUFER": [
            f"<a href='/institution/{ii.related_institutionA_id}'>{ii.related_institutionA.name}</a></br>{ii.related_institutionA.start_date.strftime('%Y') if ii.related_institutionA.start_date else ''} - {ii.related_institutionA.end_date.strftime('%Y') if ii.related_institutionA.end_date else ''}"
            for ii in institution_object.related_institutionA.filter(
                relation_type_id__in=[4203, 4202, 5, 3]
            ).order_by("start_date")
        ],
        "INSTITUTIONELLE NACHFOLGER": [
            f"<a href='/institution/{ii.related_institutionB_id}'>{ii.related_institutionB.name}</a></br>{ii.related_institutionB.start_date.strftime('%Y') if ii.related_institutionB.start_date else ''} - {ii.related_institutionB.end_date.strftime('%Y') if ii.related_institutionB.end_date else ''}"
            for ii in institution_object.related_institutionB.filter(
                relation_type_id__in=[4203, 4202, 5, 3]
            ).order_by("start_date")
        ],
    }

    return context


col_oebl = getattr(settings, "APIS_OEBL_BIO_COLLECTION", "ÖBL Biographie")
col_oebl = Collection.objects.filter(name=col_oebl)
if col_oebl.count() == 1:
    oebl_persons = Person.objects.filter(collection=col_oebl[0])
else:
    oebl_persons = Person.objects.all()

institutions = Institution.objects.all()

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
