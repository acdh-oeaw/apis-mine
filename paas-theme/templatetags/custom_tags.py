import re
from django import template
import urllib.parse

from apis_core.apis_entities.models import Institution, Place
from theme.utils import oebl_persons

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
def remove_facets(url):
    url = re.subn("&selected_facets\=[^&]+", "", url)
    return url[0]


@register.simple_tag
def filter_facetfields(fields, fieldname):
    return fields[fieldname]


@register.simple_tag
def check_facet_selection(key, val, selectedfacets):
    selectedfacet = f"{key}_exact:{val}"
    return selectedfacet in selectedfacets


@register.simple_tag
def filter_params(request, param):
    return request.GET.getlist(param)
