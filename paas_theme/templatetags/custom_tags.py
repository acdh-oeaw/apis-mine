import re
from django import template
import urllib.parse

from apis_core.apis_entities.models import Institution, Place
from paas_theme.provide_data import oebl_persons

register = template.Library()


@register.simple_tag
def people_count():
    return oebl_persons.count()


@register.simple_tag
def institution_count():
    return Institution.objects.all().count()


@register.simple_tag
def place_count():
    return Place.objects.all().count()


@register.simple_tag
def formated_daterange(startdate, enddate):
    rangestring = ""
    if (startdate and startdate is not None) or (enddate and enddate is not None):
        rangestring += "("
        if startdate and startdate is not None:
            rangestring += startdate
        if enddate and enddate is not None:
            rangestring += "-" + enddate
        rangestring += ")"
    return rangestring


@register.simple_tag
def normalize_facet(facet, kind, url=None):
    norm_kind = {
        "place_of_birth": "Geburtsort",
        "place_of_death": "Sterbeort",
        "career": "Karriere",
        "education": "Ausbildung",
        "profession": "Beruf",
        "comissions": "Kommissionen",
        "akademiemitgliedschaft": "Mitgliedschaft",
        "gender": "Geschlecht",
        "q": "Suche",
        "kind": "Typ",
    }
    fac = facet.split(":")
    fac[0] = fac[0].replace("_exact", "")
    if kind == "simple":
        return f"{norm_kind[facet]}"
    if kind == "name":
        return f"{norm_kind[fac[0].lower()]}: '{fac[1]}'"
    elif kind == "filter":
        url2 = re.sub(
            f"([\&\?]selected_facets={fac[0]}_exact)(:|%3A)({urllib.parse.quote(fac[1])})",
            "",
            url,
        )
        url2 = url2.replace("search&", "search?")
        return url2


@register.simple_tag
def normalize_filter(filter, kind, url=None):
    norm_kind = {
        "place_of_birth": "Geburtsort",
        "place_of_death": "Sterbeort",
        "career": "Karriere",
        "education": "Ausbildung",
        "profession": "Beruf",
        "comissions": "Kommissionen",
        "akademiemitgliedschaft": "Mitgliedschaft",
        "akademiefunktionen": "Akademiefunktionen",
        "gender": "Geschlecht",
        "wiss_austausch": "Wissenschaftler/innen/austausch",
        "pres_funktionen": "Funktionen im Präsidium",
        "q": "Suche",
        "start_date_form": "Mitgliedschaft von",
        "end_date_form": "Mitgliedschaft bis",
        "start_date_birth_form": "Lebensspanne von",
        "end_date_birth_form": "Lebensspanne bis",
        "mtgld_mitgliedschaft": "Mitgliedschaft",
        "mtgld_klasse": "Klasse",
    }
    bool_fields_norm = {
        "funk_praesidentin": "Präsident/in",
        "funk_vizepraesidentin": "Vizepräsident/in",
        "funk_generalsekretaerin": "Generalsekretär/in",
        "funk_sekretaerin": "Sekretär/in",
        "funk_klassenpres_math_nat": "Klassenpräsident/in math.-nat. Klasse",
        "funk_klassenpres_phil_hist": "Klassenpräsident/in phil.-hist. Klasse",
        "funk_obfrau": "Obmann/Obfrau einer Kommission",
        "funk_mitgl_kommission": "Mitglied einer Kommission",
        "funk_obfrau_kurat": "Obmann/Obfrau eines Kuratoriums/Board eines Institut/einer Forschungsstelle",
        "funk_direkt_forsch_inst": "Direktor/in eines Instituts/einer Forschungsstelle",
        "MATHEMATISCH-NATURWISSENSCHAFTLICHE": "Mathematisch-Naturwissenschaftliche Klasse",
        "PHILOSOPHISCH-HISTORISCHE": "Philosophisch-Historische Klasse",
    }
    if kind == "simple":
        return f"{norm_kind[filter['field']]}"
    if kind == "name":
        if filter["kind"] == "multi":
            val = " ODER ".join([x[1] for x in filter["value"]])
        elif filter["kind"] == "boolean":
            val = " ODER ".join(
                [
                    bool_fields_norm[x] if x in bool_fields_norm.keys() else x
                    for x in filter["value"]
                ]
            )
        else:
            val = filter["value"]
        if filter["field"].lower() in norm_kind.keys():
            return f"{norm_kind[filter['field'].lower()]}: '{val}'"
        else:
            return f"{filter['field'].title()}: '{val}'"

    elif kind == "filter":
        if filter["kind"] == "multi":
            val = [f"{x[0]}|{x[1]}" for x in filter["value"]]
        elif filter["kind"] == "boolean":
            val = [x for x in filter["value"]]
        else:
            val = [filter["value"]]
        for val1 in val:
            if isinstance(val1, str):
                url = re.sub(
                    f"([\&\?]{filter['field']}=)({urllib.parse.quote(val1)})",
                    "",
                    url,
                )
        url = url.replace("search&", "search?")
        return url


@register.simple_tag
def remove_facets(url):
    url = re.subn("&selected_facets\=[^&]+", "", url)
    return url[0]


@register.simple_tag
def filter_facetfields(fields, fieldname):
    print(fields)
    return fields[fieldname]


@register.simple_tag
def check_facet_selection(key, val, selectedfacets, vals):
    selectedfacet = f"{key}_exact:{val}"
    c1 = 0
    selected = ""
    for v in vals:
        if isinstance(v, tuple):
            if v[1] > 0:
                c1 += 1
                selected = v[0]
    return selectedfacet in selectedfacets or (c1 == 1 and val == selected)


@register.simple_tag
def filter_params(request, param):
    return request.GET.getlist(param)


@register.simple_tag
def normalize_key(value):
    new_val = value.replace("_", " ")
    return new_val


@register.simple_tag
def election(institutions):
    return [x for x in institutions if x.relation_type.id in (42, 43, 46, 35, 36, 33)]


@register.simple_tag
def abbreviate(value):
    print(value.name)
    if value.name == "MATHEMATISCH-NATURWISSENSCHAFTLICHE KLASSE":
        return "mat.-nat. Klasse"
    elif value.name == "PHILOSOPHISCH-HISTORISCHE KLASSE":
        return "phil.-hist. Klasse"
    else:
        return value
