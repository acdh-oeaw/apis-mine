import re

def abbreviate(value):
    """takes a institution objects and returns the abbreviation of the name

    Args:
        value (object): institution object

    Returns:
        string: abbreviated name of institution
    """    
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
    elif value.name == "GESAMTAKADEMIE":
        return "Gesamtakademie"
    elif value.name == "Wirkliches Mitglied (w. M.)":
        return "wM"
    elif value.name == "Korrespondierendes Mitglied im Ausland (k. M. A.)":
        return "kMA"
    elif value.name == "Korrespondierendes Mitglied im Inland (k. M. I.)":
        return "kMI"
    elif value.name == "Ehrenmitglied (E. M.)":
        return "EM"
    else:
        return value


def get_mitgliedschaft_from_relation(rel, abbreviate=True):
    """takes a PersonInstitutionRelation and returns the membership

    Args:
        rel (object): PersonInstitutionRelation
        abbreviate (bool, optional): whether to abbreviate the membership (eg kmI). Defaults to True.

    Returns:
        str: name of the membership
    """    
    lbl = rel.label.split(">>")[1].strip()
    if rel.label.split(">>")[0].strip() != "Mitglied" and not rel.label.split(">>")[0].strip().startswith('wird vorgeschlagen von'):
        return None
    if abbreviate:
        if lbl == "Mitglied der Jungen Kurie":
            return "Junge Kurie/Junge Akademie"
        res = re.search(r"\((.+)\)", lbl)
        return res.group(1)
    else:
        return lbl