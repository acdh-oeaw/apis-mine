from django.db import models
from collections.abc import Sequence
import typing
from enum import Enum

from apis_core.apis_entities.models import Person, Place, Institution
from apis_core.apis_relations.models import PersonInstitution
from apis_core.apis_vocabularies.models import PersonInstitutionRelation, PersonPlaceRelation
import datetime
import re

from zmq import proxy

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


class MitgliedschaftDict(typing.TypedDict):
    mitgliedschaft: str
    klasse: str
    start: datetime.date
    end: datetime.date


class MitgliedschaftInstitutionDict(typing.TypedDict):
    mitgliedschaft: str
    institution: str
    klasse: str
    start: datetime.date
    end: datetime.date



class PAASPersonQuerySet(models.QuerySet):
    """Adds paas specific query options to persons"""

    def members(
        self,
        memberships: typing.Optional[typing.List[str]] = None,
        institutions: typing.Optional[typing.Union[str, int]] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs
    ) -> "PAASPersonQuerySet":
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

    def get_memberships(
        self,
        relations: typing.Optional[typing.List[int]] = None,
        memberships: typing.Optional[typing.List[str]] = None,
        institutions: typing.Optional[typing.List[int]] = None, 
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
    ) -> typing.List[MitgliedschaftDict]:
        """Function to return list of memberships

        Args:
            relations (list, optional): list of ids of PersonInstitutionRelation objects used for the membership. Defaults to MITGLIEDSCHAFT.
            memberships (list, otional): List of substrings to filter the Mitgliedschaften for, defaults to all.
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
                if memberships is not None:
                    for t1 in memberships:
                        if t1.lower() in pi.label.lower():
                            ids.append(pi.pk)
                            break
                else:
                    ids.append(pi.pk)

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

    objects = PAASPersonQuerySet.as_manager()

    class Meta:
        proxy = True
        default_manager_name = "objects"



class PAASMembershipsQuerySet(models.QuerySet):

    def get_person_ids(self):
        return list(self.values_list('related_person_id', flat=True))

    def get_memberships(
        self,
        memberships: typing.Union[typing.List[str], typing.List[int], None] = None,
        institutions: typing.Union[typing.List[str], typing.List[int], None] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs
    ) -> "PAASMembershipsQuerySet":
        """Adds the possibility to filter for memberships

        Args:
            memberships (list of strings or ints, optional): filters either for substring in the membership label or uses ids when int. Defaults to None.
            institutions (list of strings or int, optional): filters for the institution (Klasse or Gesamtakademie) either by substring or id. Defaults to None.
            start (str, optional): start date. Needs to be in YYYY-MM-DD format. Defaults to None.
            end (str, optional): end date. Needs to be in YYYY-MM-DD format. Defaults to None.

        Returns:
            PAASMembership: Subclass of apis_core.apis_relations.models.PersonInstitution
        """
        q_dict = dict()
        if memberships is None:
            q_dict["relation_type_id__in"] = getattr(id_mapping, "MITGLIEDSCHAFT")
        else:
            if isinstance(memberships[0], str): 
                ids = []
                for pi in PersonInstitutionRelation.objects.filter(pk__in=getattr(id_mapping, "MITGLIEDSCHAFT")):
                    for t1 in memberships:
                        if t1.lower() in pi.label.lower():
                            ids.append(pi.pk)
                            break
                q_dict["relation_type_id__in"] = ids
            elif isinstance(memberships[0], int):
                q_dict["relation_type_id__in"] = memberships 
        if institutions is not None:
            if len(institutions) > 0:
                ids = []
                if isinstance(institutions[0], str):
                    for inst in Institution.objects.filter(id__in=getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")):
                        for inst2 in institutions:
                            if inst2.lower() in inst.name.lower():
                                ids.append(inst.id)
                                break
                    q_dict["related_institution_id__in"] = institutions
            else:
                q_dict["related_institution_id__in"] = getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN") 
        else:
            q_dict["related_institution_id__in"] = getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN") 
        if start is not None:
            if end is None or end == "":
                end = datetime.datetime.today().strftime("%Y-%m-%d")
            if start > end:
                raise ValueError(f"End date needs to be before start date: {start} > {end}")
            q_dict["start_date__lte"] = convert_date(end)
            q_dict["end_date__gte"] = convert_date(start)
        return self.filter(**q_dict)


class PAASMembership(PersonInstitution):

    objects = PAASMembershipsQuerySet.as_manager()

    class Meta:
        proxy = True
        default_manager_name = "objects"


class PAASInstitution(Institution):
    """ORM class for Institutions in PAAS

    Args:
        Institution (_type_): _description_
    """

    def is_academy_institution(self):
        """test if institution is an academy institution

        Returns:
            boolean: True if it is an academy institution, False if it isnt
        """        

        if self.kind_id in getattr(id_mapping, "INSTITUTION_TYPE_AKADEMIE"):
            return True
        else: return False

    def get_members(
        self,
        members: typing.Union[typing.List[typing.Literal['president', 'member']], typing.List[int], None] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs) -> "PersonInstitution":

        q_dict = dict()
        if members is not None:
            if len(members) > 0:
                if isinstance(members[0], str):
                    members_new = []
                    for mem in members:
                        members_new.extend(getattr(id_mapping, "INSTITUTION_MEMBERS_TYPES")[mem])
                    q_dict["related_person_id__in"] = members_new
        
        if start is not None:
            if end is None or end == "":
                end = datetime.datetime.today().strftime("%Y-%m-%d")
            if start > end:
                raise ValueError(f"End date needs to be before start date: {start} > {end}")
            q_dict["start_date__lte"] = convert_date(end)
            q_dict["end_date__gte"] = convert_date(start)
        return self.personinstitution_set.filter(**q_dict)

    def get_members_persons(
        self,
        members: typing.Union[typing.List[typing.Literal['president', 'member']], typing.List[int], None] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs) -> "PAASPersonQuerySet":

        ids = list(set(self.get_members(members=members, start=start, end=end).values_list("related_person_id", flat=True)))
        return PAASPerson.objects.filter(id__in=ids)

    def get_memberships_dict(
        self,
        members: typing.Union[typing.List[typing.Literal['president', 'member']], typing.List[int], None] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs) -> typing.Union[typing.List[MitgliedschaftInstitutionDict], None]:

        res = []
        for memb in self.get_members(members=members, start=start, end=end):
            res.append({
                "mitgliedschaft": str(memb.relation_type),
                "institution": str(self),
                "klasse": str(self.get_klasse()),
                "start": memb.start,
                "end": memb.end
            })



    class Meta:
        proxy = True
        default_manager_name = "objects"