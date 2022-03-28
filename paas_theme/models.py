from django.db import models
from collections.abc import Sequence
import typing

from apis_core.apis_entities.models import Person, Place, Institution
from apis_core.apis_vocabularies.models import PersonInstitutionRelation, PersonPlaceRelation
import datetime
import re

# from .provide_data import classes
from paas_theme import id_mapping

# from .id_mapping import GESAMTAKADEMIE_UND_KLASSEN, MITGLIEDSCHAFT
from .helper_functions import abbreviate, get_mitgliedschaft_from_relation


def convert_date(date):
    """converts date string to correct format

    Args:
        date (str): date string

    Returns:
        str: returns date in format YYYY-MM-DD
    """

    if re.match(r"^[0-9]{4}$", date):
        return f"{date}-06-30"
    elif re.match(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", date):
        pdate = re.match(r"([0-9]{2})\.([0-9]{2})\.([0-9]{4})", date)
        return f"{pdate.group(3)}-{pdate.group(2)}-{pdate.group(1)}"
    else:
        return date


class PaasQuerySet(models.QuerySet):
    """Adds paas specific query options to persons"""

    def members(
        self,
        memberships: typing.Optional[typing.List[str]] = None,
        institutions: typing.Optional[typing.Union[str, int]] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs
    ) -> "PAASPerson":
        """filter for retrieving only members of the academy

        Args:
            memberships (list of strings, optional): allows to set an array of strings to filter by. Defaults to None.
            start (string, optional): string in the format of YYYY-MM-DD or YYYY for filtering memberships in this period. Defaults to None.
            end (string, optional): string in the format of YYYY-MM-DD or YYYY for filtering memberships in this period. Defaults to None or today if start is not None.

        Returns:
            PAASPerson: _description_
        """
        ids = getattr(id_mapping, "MITGLIEDSCHAFT")
        if memberships is not None:
            ids = []
            for pi in PersonInstitutionRelation.objects.filter(pk__in=getattr(id_mapping, "MITGLIEDSCHAFT")):
                for t1 in memberships:
                    if t1.lower() in pi.label.lower():
                        ids.append(pi.pk)
                        break
        if start is None and end is None and institutions is None:
            return self.filter(personinstitution_set__relation_type_id__in=ids).distinct()
        qs = self.annotate(
            members=models.FilteredRelation(
                "personinstitution_set",
                condition=models.Q(personinstitution_set__relation_type_id__in=ids),
            )
        )
        qdict2 = {}
        if start is not None or end is not None:
            if end is None:
                end = datetime.datetime.today().strftime("%Y-%m-%d")
            if start is None:
                start = "1600-01-01"
            qdict2["members__start_date__lte"] = convert_date(end)
            qdict2["members__end_date__gte"] = convert_date(start)
        if institutions is not None:
            if isinstance(institutions[0], str):
                institutions = list(Institution.objects.filter(name__in=institutions).values("pk", flat=True))
            qdict2["members__related_institution_id__in"] = institutions
        for k, v in kwargs.items():
            qdict2[k] = v
        return qs.filter(**qdict2).distinct()



class PAASFilterManager(models.Manager):
    """manager used to carry the additional queries"""

    def get_queryset(self):
        return PaasQuerySet(self.model, using=self._db)

    def members(
        self,
        memberships: typing.Optional[typing.List[str]] = None, 
        institutions: typing.Optional[typing.Union[str, int]] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs
    ) -> "PAASPerson":
        """filter for members

        Args:
            memberships (list of strings, optional): list of strings to query for in membership relation labels. Defaults to None.

        Returns:
            PAASPerson: returns queryset of PAASPersons
        """
        return self.get_queryset().members(
            memberships=memberships, start=start, end=end, institutions=institutions, **kwargs
        )


class PAASPerson(Person):
    """Subclass of APIS Person used to attach PAAS specific functions"""

    def is_member(self, relations=None, institutions=None, start=None, end=None):
        """Function to test whther the person is member or not

        Args:
            relations (list, optional): list of ids of PersonInstitutionRelation objects used for the membership. Defaults to MITGLIEDSCHAFT.
            institutions (list, optional): list of ids of Institution objects used for membership. Defaults to GESAMTAKADEMIE_UND_KLASSEN.
            start (str, optional): datestring used for limiting the test to a certain perion (YYYY or YYYY-MM-DD). Defaults to None.
            end (str, optional): datestring used for limiting the test to a certain perion (YYYY or YYYY-MM-DD). Defaults to None.

        Returns:
            boolean: returns True or False
        """
        if relations is None:
            relations = getattr(id_mapping, "MITGLIEDSCHAFT")
        if institutions is None:
            institutions = getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")
        qd = {
            "related_institution_id__in": institutions,
            "relation_type_id__in": relations,
        }
        if start is not None:
            if end is None:
                end = datetime.datetime.now().strftime("%Y-%m-%d")
            qd["start_date__lte"] = convert_date(end)
            qd["start_date__gte"] = convert_date(start)
        return self.personinstitution_set.filter(**qd).count() > 0

    def get_memberships(self, relations=None, institutions=None, start=None, end=None):
        """Function to return list of memberships

        Args:
            relations (list, optional): list of ids of PersonInstitutionRelation objects used for the membership. Defaults to MITGLIEDSCHAFT.
            institutions (list, optional): list of ids of Institution objects used for membership. Defaults to GESAMTAKADEMIE_UND_KLASSEN.
            start (str, optional): datestring used for limiting the test to a certain perion (YYYY or YYYY-MM-DD). Defaults to None.
            end (str, optional): datestring used for limiting the test to a certain perion (YYYY or YYYY-MM-DD). Defaults to None.

        Returns:
            list: list of dict {'mitgliedschaft': XX, 'klasse': XX, 'start': XX, 'end': XX}
        """

        ids = getattr(id_mapping, "MITGLIEDSCHAFT")
        if relations is not None:
            ids = []
            for pi in PersonInstitutionRelation.objects.filter(pk__in=getattr(id_mapping, "MITGLIEDSCHAFT")):
                for t1 in memberships:
                    if t1.lower() in pi.label.lower():
                        ids.append(pi.pk)
                        break
        if institutions is None:
            institutions = getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")

        qd = {
            "related_institution_id__in": institutions,
            "relation_type_id__in": ids,
        }
        if start is not None:
            if end is None:
                end = datetime.datetime.now().strftime("%Y-%m-%d")
            qd["start_date__lte"] = convert_date(end)
            qd["start_date__gte"] = convert_date(start)
        res = []
        for rel in self.personinstitution_set.filter(**qd).order_by("start_date"):
            kls = abbreviate(rel.related_institution)
            memb = get_mitgliedschaft_from_relation(rel.relation_type)
            res.append(
                {
                    "klasse": kls,
                    "mitgliedschaft": memb,
                    "start": rel.start_date,
                    "end": rel.end_date,
                }
            )
        return res
    
    def get_place_of_birth(self, include_country: bool=False) -> typing.Union[Place, typing.Tuple[Place, Place]]:
        """returns the place of birth of a person

        Args:
            include_country (bool, optional): whether to include the country of birth in the return. Defaults to False.

        Returns:
            typing.Union[Place, typing.Tuple[Place, Place]]: returns either a tuple of two places: place of birth and country of birth or a Place
        """

        geburtsort = getattr(id_mapping, "RELATION_GEBURTSORT")
        located_in = getattr(id_mapping, "GELEGEN_IN")

        birth_place = self.personplace_set.filter(relation_type_id__in=geburtsort)
        if birth_place.count() != 1:
            return None
        birth_place = birth_place[0].related_place

        if include_country:
            birth_country = birth_place.related_placeB.filter(relation_type_id__in=located_in)
            if birth_country.count() == 1:
                birth_country = birth_country[0].related_placeB
            else:
                birth_country = None
            return (birth_place, birth_country)
        return birth_place

    def nobelprizes(self) -> typing.Union[None, typing.List[typing.Tuple[datetime.date, str, Institution]]]:
        nobelpreise = getattr(id_mapping, "NOBEL_PREISE")
        preistr = getattr(id_mapping, "RELATION_PREISTRAEGER")
        nb = self.personinstitution_set.filter(related_institution_id__in=nobelpreise, relation_type_id__in=preistr)
        if nb.count() == 0:
            return None
        else:
            res = []
            for nb1 in nb:
                res.append((nb1.start_date, nb1.related_institution.name, nb1.related_institution))
            return res

    objects = PAASFilterManager()

    class Meta:
        proxy = True
        default_manager_name = "objects"
