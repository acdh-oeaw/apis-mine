import datetime
import pandas as pd

from apis_core.apis_relations.models import PersonInstitution, PersonPerson
from . id_mapping import NSDAP, KLASSEN_IDS
from . provide_data import NATIONALSOZIALISTEN, KOMMISSIONEN, get_child_classes, PersonPersonRelation


def make_full_name(row, prop_name, prop_first_name):
    return ", ".join([row[prop_name], row[prop_first_name]])


props = [
    'related_person__id',
    'related_person__name',
    'related_person__first_name',
    'related_person__start_date',
    'relation_type__name',
    'relation_type__parent_class__name',
    'related_institution__id',
    'related_institution__name',
    'start_date',
    'end_date'
]

person_person_props = [
    'related_personA__id',
    'related_personA__name',
    'related_personA__first_name',
    'relation_type__id',
    'relation_type__name',
    'relation_type__parent_class__name',
    'start_date',
    'related_personB__id',
    'related_personB__name',
    'related_personB__first_name',
    'end_date'
]

def proposed_by_nazi_data():
    pers_pers = PersonPerson.objects.filter(
        relation_type__in=get_child_classes([3141], PersonPersonRelation),
        related_personB_id__in=NATIONALSOZIALISTEN,
        start_date__gte='1938-03-01'
    ).values_list(*person_person_props)
    orig_df = pd.DataFrame(pers_pers, columns=person_person_props)
    orig_df['gewähltes Mitglied'] = orig_df.apply(
        lambda row: make_full_name(row, 'related_personA__name', 'related_personA__first_name') , axis=1
    )
    orig_df['NSDAP Mitglied'] = orig_df.apply(
        lambda row: make_full_name(row, 'related_personB__name', 'related_personB__first_name') , axis=1
    )
    orig_df['Wahldatum'] = orig_df['start_date']
    orig_df['Art der Mitgliedschaft'] = orig_df['relation_type__name']
    return orig_df.sort_values(by='Wahldatum')

def nazi_komm_df():
    rels = PersonInstitution.objects.filter(
            related_person__in=NATIONALSOZIALISTEN,
            related_institution__in=KOMMISSIONEN
        ).values_list(*props)
    orig_df = pd.DataFrame(list(rels), columns=props)
    return orig_df

def get_ns():
    rels = PersonInstitution.objects.filter(
            related_institution__in=NSDAP + KLASSEN_IDS,
            related_person__in=NATIONALSOZIALISTEN
        ).values_list(*props)

    orig_df = pd.DataFrame(list(rels), columns=props)
    data = []
    for gr, df in orig_df.groupby('related_person__id'):
        try:
            nsdap = df.query('related_institution__name=="Nationalsozialistische Deutsche Arbeiterpartei"').iloc[0]
        except IndexError:
            continue
        ak = df.iloc[0]
        item = {}
        item['id'] = ak['related_person__id']
        item['name'] = ak['related_person__name']
        item['first_name'] = ak['related_person__first_name']
        item['birth_date'] = ak['related_person__start_date']
        item['beitritt_nsdap'] = f"{nsdap['start_date']}"
        item['beitritt_akademie'] = f"{ak['start_date']}"
        try:
            item['illegal'] = nsdap['start_date'] < datetime.date(1938, 3, 13)
        except:
            item['illegal'] = "unklar, kein Eintrittsdatum bekannt"
        item['mitglied_vor_ns'] = ak['start_date'] < datetime.date(1939, 1, 1)
        item['mitglied_in_ns'] = datetime.date(1939, 1, 1) < ak['start_date'] and ak['start_date'] < datetime.date(1944, 12, 31)
        item['mitglied_nach_ns'] = ak['start_date'] > datetime.date(1944, 12, 31)
        data.append(item)
    return data