from itertools import chain
from platform import release
from django.db import models
from collections.abc import Sequence
import typing
from enum import Enum

from apis_core.apis_entities.models import Person, Place, Institution
from apis_core.apis_relations.models import PersonInstitution
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

class PrizeRecipientDict(typing.TypedDict):
    preistraeger: Person
    abgelehnt: bool
    date: typing.Optional[datetime.date]

class PrizeStifterDict(typing.TypedDict):
    stifter: Person
    date: typing.Optional[datetime.date]


class MitgliedschaftDict(typing.TypedDict):
    mitgliedschaft: str
    klasse: str
    start: datetime.date
    end: datetime.date


class MitgliedschaftInstitutionDict(typing.TypedDict):
    mitgliedschaft: object
    person: Person
    start: datetime.date
    end: datetime.date


class InstitutionInstitutionDict(typing.TypedDict):
    institution: str
    institution_link: str
    relation: str
    start: typing.Optional[datetime.date]
    end: typing.Optional[datetime.date]




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

    def get_class(self):
        try:
            return self.related_institutionB.get(relation_type_id=2, related_institutionB_id__in=[1, 2, 3])
        except:
            return None

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
        **kwargs) -> typing.List[MitgliedschaftInstitutionDict]:

        res = []
        for memb in self.get_members(members=members, start=start, end=end):
            res.append({
                "mitgliedschaft": memb.relation_type,
                "person": memb.related_person,
                "start": memb.start_date,
                "end": memb.end_date
            })
        return res

    def get_structure(
        self,
        relations: typing.Union[typing.List[typing.Literal['ist Teil von', 'hat Untereinheit']], typing.List[int], None] = None,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs) -> typing.List[InstitutionInstitutionDict]:

        res = []
        q_dict = {}
        if relations is None:
            q_dict["relation_type_id__in"] = getattr(id_mapping, "INSTITUTION_STRUCTURE_IDS")
        elif isinstance(relations[0], str):
            q_dict["relation_type__in"] = relations
        elif isinstance(relations[0], int):
            q_dict["relation_type_id__in"] = relations
        if start is not None:
            if end is None or end == "":
                end = datetime.datetime.today().strftime("%Y-%m-%d")
            if start > end:
                raise ValueError(f"End date needs to be before start date: {start} > {end}")
            q_dict["start_date__lte"] = convert_date(end)
            q_dict["end_date__gte"] = convert_date(start)
        for instinst in self.related_institutionA.filter(**q_dict).exclude(related_institutionA_id__in=getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")):
            res.append({
                "relation": instinst.relation_type,
                "relation_label": instinst.relation_type.label if instinst.related_institutionA == self else instinst.relation_type.label_reverse,
                "institution": instinst.related_institutionB if instinst.related_institutionA == self else instinst.related_institutionA,
                "institution_label": str(instinst.related_institutionB) if instinst.related_institutionA == self else str(instinst.related_institutionA),
                "institution_link": f"/institution/{instinst.related_institutionB_id if instinst.related_institutionA == self else instinst.related_institutionA_id}",
                "start": instinst.start_date,
                "end": instinst.end_date
            })
        for instinst in self.related_institutionB.filter(**q_dict).exclude(related_institutionB_id__in=getattr(id_mapping, "GESAMTAKADEMIE_UND_KLASSEN")):
            res.append({
                "relation": instinst.relation_type,
                "relation_label": instinst.relation_type.label if instinst.related_institutionA == self else instinst.relation_type.label_reverse,
                "institution": instinst.related_institutionB if instinst.related_institutionA == self else instinst.related_institutionA, 
                "institution_label": str(instinst.related_institutionB) if instinst.related_institutionA == self else str(instinst.related_institutionA),
                "institution_link": f"/institution/{instinst.related_institutionB_id if instinst.related_institutionA == self else instinst.related_institutionA_id}",
                "start": instinst.start_date,
                "end": instinst.end_date
            })
        try: 
            res = sorted(res, key=lambda d: d['start']) 
        except:
            pass
        return res

    def get_prize_recipients(
        self,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs
    ) -> typing.Optional[typing.List[PrizeRecipientDict]]:
        return [{"preistraeger": x.related_person, "date": x.start_date, "abgelehnt": True if x.relation_type_id in getattr(id_mapping, "RELATION_PREISTRAEGER_ABGELEHNT") else False} for x in self.personinstitution_set.filter(relation_type_id__in=getattr(id_mapping, "RELATION_PREISTRAEGER")+getattr(id_mapping, "RELATION_PREISTRAEGER_ABGELEHNT"))]


    def get_prize_stifter(
        self,
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        **kwargs
    ) -> typing.Optional[typing.List[PrizeStifterDict]]:
        return [{"stifter": x.related_person, "date": x.start_date} for x in self.personinstitution_set.filter(relation_type_id__in=getattr(id_mapping, "RELATION_PREIS_STIFTER"))]


    def _get_relation_label_history(self, relation, relations_query: typing.List[typing.Literal["Institutionelle Vorläufer", "Institutionelle Nachfolger"]] = ["Institutionelle Vorläufer", "Institutionelle Nachfolger"]):
        if relation.related_institutionA == self: # normal direction
            if relation.relation_type_id in getattr(id_mapping, "INSTITUTION_HISTORY_IDS")["Institutionelle Vorläufer"] and "Institutionelle Vorläufer" in relations_query:
                label_relation = "Institutionelle Vorläufer"
            elif relation.relation_type_id in getattr(id_mapping, "INSTITUTION_HISTORY_IDS")["Institutionelle Nachfolger"] and "Institutionelle Nachfolger" in relations_query:
                label_relation = "Institutionelle Nachfolger"
            else:
                label_relation = None
        else:
            if relation.relation_type_id in getattr(id_mapping, "INSTITUTION_HISTORY_IDS")["Institutionelle Vorläufer"] and "Institutionelle Nachfolger" in relations_query:
                label_relation = "Institutionelle Nachfolger"
            elif relation.relation_type_id in getattr(id_mapping, "INSTITUTION_HISTORY_IDS")["Institutionelle Nachfolger"] and "Institutionelle Vorläufer" in relations_query:
                label_relation = "Institutionelle Vorläufer"
            else:
                label_relation = None
        return label_relation


    def get_history(
        self,
        relations: typing.List[typing.Literal['Institutionelle Vorläufer', 'Institutionelle Nachfolger']] = ['Institutionelle Vorläufer', 'Institutionelle Nachfolger'],
        start: typing.Optional[str] = None,
        end: typing.Optional[str] = None,
        full_history: bool = True,
        **kwargs) -> typing.List[InstitutionInstitutionDict]:

        res = []
        q_dictA = {}
        q_dictB = {}
        q_dictA["relation_type_id__in"] = q_dictB["relation_type_id__in"] = list(chain.from_iterable([getattr(id_mapping, "INSTITUTION_HISTORY_IDS")[rel_ids] for rel_ids in relations]))
        if len(relations) < 2:
            q_dictA["relation_type_id__in"] = list(chain.from_iterable([getattr(id_mapping, "INSTITUTION_HISTORY_IDS")[rel_ids] for rel_ids in relations]))
            q_dictB["relation_type_id__in"] = list(set(chain.from_iterable([x for x in getattr(id_mapping, "INSTITUTION_HISTORY_IDS").values()])) - set(chain.from_iterable([getattr(id_mapping, "INSTITUTION_HISTORY_IDS")[rel_ids] for rel_ids in relations])))
        if start is not None:
            if end is None or end == "":
                end = datetime.datetime.today().strftime("%Y-%m-%d")
            if start > end:
                raise ValueError(f"End date needs to be before start date: {start} > {end}")
            q_dictA["start_date__lte"] = convert_date(end)
            q_dictA["end_date__gte"] = convert_date(start)
            q_dictB["start_date__lte"] = convert_date(end)
            q_dictB["end_date__gte"] = convert_date(start)
        for instinst in self.related_institutionA.filter(**q_dictB):
            label_relation = self._get_relation_label_history(instinst, relations)
            if label_relation is None:
                continue
            res.append({
                "relation": label_relation,
                "relation_label": str(instinst.relation_type) if instinst.related_institutionA == self else str(instinst.relation_type.name_reverse),
                "institution": instinst.related_institutionB if instinst.related_institutionA == self else instinst.related_institutionA,
                "institution_label": str(instinst.related_institutionB) if instinst.related_institutionA == self else str(instinst.related_institutionA),
                "institution_link": f"/institution/{instinst.related_institutionB_id if instinst.related_institutionA == self else instinst.related_institutionA_id}",
                "start": instinst.start_date,
                "end": instinst.end_date,
                "start_date_related_institution": instinst.related_institutionB.start_date if instinst.related_institutionA == self else instinst.related_institutionA.start_date,
                "end_date_related_institution": instinst.related_institutionB.end_date if instinst.related_institutionA == self else instinst.related_institutionA.end_date
            })
        for instinst in self.related_institutionB.filter(**q_dictA):
            label_relation = self._get_relation_label_history(instinst, relations)
            if label_relation is None:
                continue
            res.append({
                "relation": label_relation,
                "relation_label": str(instinst.relation_type) if instinst.related_institutionA == self else str(instinst.relation_type.name_reverse),
                "institution": instinst.related_institutionB if instinst.related_institutionA == self else instinst.related_institutionA,
                "institution_label": str(instinst.related_institutionB) if instinst.related_institutionA == self else str(instinst.related_institutionA),
                "institution_link": f"/institution/{instinst.related_institutionB_id if instinst.related_institutionA == self else instinst.related_institutionA_id}",
                "start": instinst.start_date,
                "end": instinst.end_date,
                "start_date_related_institution": instinst.related_institutionB.start_date if instinst.related_institutionA == self else instinst.related_institutionA.start_date,
                "end_date_related_institution": instinst.related_institutionB.end_date if instinst.related_institutionA == self else instinst.related_institutionA.end_date
            })
        if full_history:
            for instA in res:
                res_2 = PAASInstitution.objects.get(pk=instA["institution"].pk).get_history(relations=[instA["relation"]])
                for res_3 in res_2:
                    if res_3 not in res:
                        res.append(res_3)
        res = sorted(res, key=lambda d: d['start']) 
        return res
    
    def get_website_data(self, res=None):
        vor_nachf = self.get_history()
        lst_vor = []
        lst_nach = []
        if res is None:
            res = {"daten_institution": {}}
        else:
            res["daten_institution"] = {}
        for x in vor_nachf:
            if x["relation"] == "Institutionelle Vorläufer":
                lst_vor.append(x)
            else:
                lst_nach.append(x)
        if len(lst_vor) > 0:
            res["daten_institution"]["INSTITUTIONELLE VORLÄUFER"] = [f"{lst_vor[-1]['relation_label']} <a href='{lst_vor[-1]['institution_link']}'>{lst_vor[-1]['institution_label']}</a></br>{lst_vor[-1]['start_date_related_institution'].strftime('%Y') if lst_vor[-1]['start_date_related_institution'] else ''} - {lst_vor[-1]['end_date_related_institution'].strftime('%Y') if lst_vor[-1]['end_date_related_institution'] else ''}"]
        if len(lst_nach) > 0:
            res["daten_institution"]["INSTITUTIONELLE NACHFOLGER"] = [f"{lst_nach[0]['relation_label']} <a href='{lst_nach[0]['institution_link']}'>{lst_nach[0]['institution_label']}</a></br>{lst_nach[0]['start_date_related_institution'].strftime('%Y') if lst_nach[0]['start_date_related_institution'] else ''} - {lst_nach[0]['end_date_related_institution'].strftime('%Y') if lst_nach[0]['end_date_related_institution'] else ''}"]
        if len(lst_vor) > 1:
            res["daten_institution"]["INSTITUTIONELLE VORLÄUFER"] = [f"<a href='{ii['institution_link']}'>{ii['institution_label']}</a></br>{ii['start_date_related_institution'].strftime('%Y') if ii['start_date_related_institution'] else ''} - {ii['end_date_related_institution'].strftime('%Y') if ii['end_date_related_institution'] else ''}" for ii in lst_vor[:-1]] + res["daten_institution"]["INSTITUTIONELLE VORLÄUFER"]
        if len(lst_nach) > 1:
            res["daten_institution"]["INSTITUTIONELLE NACHFOLGER"].extend([f"<a href='{ii['institution_link']}'>{ii['institution_label']}</a></br>{ii['start_date_related_institution'].strftime('%Y') if ii['start_date_related_institution'] else ''} - {ii['end_date_related_institution'].strftime('%Y') if ii['end_date_related_institution'] else ''}" for ii in lst_nach[1:]])
        if self.kind_id in getattr(id_mapping, "INSTITUTION_TYPE_AKADEMIE"):
            obm = []
            mitgld = []
            for mem in self.get_memberships_dict():
                for k, v in getattr(id_mapping, "INSTITUTION_TYPE_MEMBERSHIP").items():
                    if mem["mitgliedschaft"].id in v:
                        if k not in res["daten_institution"].keys():
                            res["daten_institution"][k] = []
                        res["daten_institution"][k].append(f"<a href='/person/{mem['person'].id}'>{mem['person']}<a/> {'(Stv.)' if 'stellvertreter' in str(mem['mitgliedschaft']).lower() else ''} {mem['start'].strftime('%Y') if mem['start'] else ''} - {mem['end'].strftime('%Y') if mem['end'] else ''}")
        res["struktur"] = []
        for struc in self.get_structure():
            res["struktur"].append(
                f"{struc['relation_label']} <a href='{struc['institution_link']}'>{struc['institution_label']}</a> {struc['start'].strftime('%Y') if struc['start'] else ''}{' - ' + struc['end'].strftime('%Y') if struc['end'] else ''}"
            )
        related_inst = list(self.related_institutionB.filter(related_institutionB_id__in=[1,2,3], relation_type_id__in=[2, 99]).order_by('start_date')) + list(self.related_institutionA.filter(related_institutionB_id__in=[1,2,3], relation_type_id__in=[2, 99]).order_by('start_date'))
        if len(related_inst) == 1:
            related_inst = related_inst[0].related_institutionB
            res["untertitel"] = f"{self.kind.name}{' der ' + str(related_inst) if related_inst else ''}"
        elif len(related_inst) > 1:
            lst_untertitel = []
            for rel_inst_2 in related_inst:
                lst_untertitel.append(f"{self.kind.name}{' der ' + str(rel_inst_2.related_institutionB) if rel_inst_2.related_institutionB else ''} {rel_inst_2.start_date.strftime('%Y') if rel_inst_2.start_date else ''} - {rel_inst_2.end_date.strftime('%Y') if rel_inst_2.end_date else ''}")
            res["untertitel"] = "<br/>".join(lst_untertitel)
        else:
            res["untertitel"] = "" if self.kind is None else self.kind.name
        if self.kind_id in getattr(id_mapping, "INSTITUTION_TYPE_PREISE"):
            res["daten_institution"]["PREISTRÄGERINNEN / PREISTRÄGER"] = []
            for preis in self.get_prize_recipients():
                res["daten_institution"]["PREISTRÄGERINNEN / PREISTRÄGER"].append(
                    f"<a href='/person/{preis['preistraeger'].id}'>{str(preis['preistraeger'])}</a>{' '+preis['date'].strftime('%Y') if preis['date'] is not None else ''}{' lehnt Preis ab' if preis['abgelehnt'] else ''}"
                )
            stifter = self.get_prize_stifter()
            if len(stifter) > 0:
                res["daten_institution"]["STIFTERINNEN / STIFTER"] = []
                for stifter_pers in stifter:
                    res["daten_institution"]["STIFTERINNEN / STIFTER"].append(
                        f"<a href='/person/{stifter_pers['stifter'].id}'>{str(stifter_pers['stifter'])}</a>{' '+stifter_pers['date'].strftime('%Y') if stifter_pers['date'] is not None else ''}"
                    )    
        return res

    class Meta:
        proxy = True
        default_manager_name = "objects"