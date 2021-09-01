import datetime
import pandas as pd

from apis_core.apis_relations.models import PersonInstitution
from . id_mapping import NSDAP, KLASSEN_IDS
from . provide_data import NATIONALSOZIALISTEN


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
        # for x in props[:3]:
        #     item[x] = ak[x]
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