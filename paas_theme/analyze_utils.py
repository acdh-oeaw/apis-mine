import datetime
import pandas as pd

from django.db.models import Count

from apis_core.apis_relations.models import PersonInstitution, PersonPerson
from . id_mapping import NSDAP, KLASSEN_IDS, RUHEND_GESTELLT
from . provide_data import MITGLIEDER, NATIONALSOZIALISTEN, KOMMISSIONEN, get_child_classes, PersonPersonRelation


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


def kommission_mitglied_per_year(
    start_year=1846,
    end_year=2020,
    person=MITGLIEDER,
    inst=KOMMISSIONEN,
):
    time = {}
    for i in range(start_year, end_year):
        time[i] = 0
    komm = {}
    for x in KOMMISSIONEN:
        komm[x.name] = dict(time)
        komm[x.name]['id'] = x.id
    for year in range(start_year, end_year):
        rels = PersonInstitution.objects.filter(
            related_person__in=person,
            related_institution__in=inst,
            start_date__year__lte=year,
            end_date__year__gte=year
        ).values_list(*['related_institution__name', 'related_institution__id']).annotate(Count('related_person_id'))
        for x in rels:
            komm_entry = komm[x[0]]
            komm_entry[year] = x[2]
    series = []
    for key, value in komm.items():
        item = {
            'name': key
        }
        item['data'] = [x[1] for x in value.items() if isinstance(x[0], int)]
        series.append(item)
    return series

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


def ruhend_gestellt_df():
    rels = PersonInstitution.objects.filter(
            related_person__in=NATIONALSOZIALISTEN,
            relation_type__in=RUHEND_GESTELLT
        ).values_list(*props)
    df = pd.DataFrame(list(rels), columns=props)
    df['Name'] = df.apply(
    lambda row: make_full_name(row, 'related_person__name', 'related_person__first_name') , axis=1
)
    return df

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