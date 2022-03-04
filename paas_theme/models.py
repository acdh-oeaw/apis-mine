from django.db import models
from collections.abc import Sequence
import typing

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import PersonInstitutionRelation
import datetime
import re
#from .provide_data import classes
from .id_mapping import GESAMTAKADEMIE_UND_KLASSEN, MITGLIEDSCHAFT
from .helper_functions import abbreviate, get_mitgliedschaft_from_relation


def convert_date(date):
    """converts date string to correct format

    Args:
        date (str): date string

    Returns:
        str: returns date in format YYYY-MM-DD
    """

    if re.match(r'^[0-9]{4}$', date):
        return f"{date}-06-30"
    elif re.match(r'[0-9]{2}\.[0-9]{2}\.[0-9]{4}', date):
        pdate = re.match(r'([0-9]{2})\.([0-9]{2})\.([0-9]{4})', date)
        return f"{pdate.group(3)}-{pdate.group(2)}-{pdate.group(1)}"
    else:
        return date

class PaasQuerySet(models.QuerySet):
    """Adds paas specific query options to persons
    """

    def members(self, memberships: typing.Optional[typing.List[str]]=None, start: typing.Optional[str]=None, end: typing.Optional[str]=None) -> 'PAASPerson':
        """filter for retrieving only members of the academy

        Args:
            memberships (list of strings, optional): allows to set an array of strings to filter by. Defaults to None.
            start (string, optional): string in the format of YYYY-MM-DD or YYYY for filtering memberships in this period. Defaults to None.
            end (string, optional): string in the format of YYYY-MM-DD or YYYY for filtering memberships in this period. Defaults to None or today if start is not None.

        Returns:
            PAASPerson: _description_
        """        
        ids = MITGLIEDSCHAFT
        if memberships is not None:
            ids = []
            for pi in PersonInstitutionRelation.objects.filter(pk__in=MITGLIEDSCHAFT):
                for t1 in memberships:
                    if t1.lower() in pi.label.lower():
                        ids.append(pi.pk)
                        break
        if start is not None or end is not None:
            qs = self.annotate(members=models.FilteredRelation("personinstitution_set", condition=models.Q(personinstitution_set__relation_type_id__in=ids)))
            if end is None:
                end = datetime.datetime.today().strftime("%Y-%m-%d")
            if start is None:
                start = "1600-01-01"
            return qs.filter(members__start_date__lte=convert_date(end), members__end_date__gte=convert_date(start)).distinct()

        return self.filter(personinstitution_set__relation_type_id__in=ids).distinct()

class PAASFilterManager(models.Manager):
    """manager used to carry the additional queries
    """    
    
    def get_queryset(self):
        return PaasQuerySet(self.model, using=self._db)

    def members(self, memberships: typing.Optional[typing.List[str]]=None, start: typing.Optional[str]=None, end: typing.Optional[str]=None) -> 'PAASPerson':
        """filter for members

        Args:
            memberships (list of strings, optional): list of strings to query for in membership relation labels. Defaults to None.

        Returns:
            PAASPerson: returns queryset of PAASPersons
        """        
        return self.get_queryset().members(memberships=memberships, start=start, end=end)

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
            relations = MITGLIEDSCHAFT
        if institutions is None:
            institutions = GESAMTAKADEMIE_UND_KLASSEN
        qd = {
            'related_institution_id__in': institutions,
            'relation_type_id__in': relations 
            }
        if start is not None:
            if end is None:
                end = datetime.datetime.now().strftime('%Y-%m-%d')
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

        if relations is None:
            relations = MITGLIEDSCHAFT
        if institutions is None:
            institutions = GESAMTAKADEMIE_UND_KLASSEN

        qd = {
            'related_institution_id__in': institutions,
            'relation_type_id__in': relations 
            }
        if start is not None:
            if end is None:
                end = datetime.datetime.now().strftime('%Y-%m-%d')
            qd["start_date__lte"] = convert_date(end)
            qd["start_date__gte"] = convert_date(start)
        res = []
        for rel in self.personinstitution_set.filter(**qd).order_by('start_date'):
            kls = abbreviate(rel.related_institution)
            memb = get_mitgliedschaft_from_relation(rel.relation_type)
            res.append(
                {
                    'klasse': kls,
                    'mitgliedschaft': memb,
                    'start': rel.start_date,
                    'end': rel.end_date
                }
            )
        return res

    objects = PAASFilterManager() 
    class Meta:
        proxy = True
        default_manager_name = 'objects'