import datetime
import pandas as pd

from django.http import JsonResponse

from apis_core.apis_relations.models import PersonInstitution
from . id_mapping import NSDAP, KLASSEN_IDS
from . provide_data import NATIONALSOZIALISTEN, KOMMISSIONEN

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


def get_nazi_kommissionen(request):
    rels = PersonInstitution.objects.filter(
        related_person__in=NATIONALSOZIALISTEN,
        related_institution__in=KOMMISSIONEN
    ).values_list(*props)
    orig_df = pd.DataFrame(list(rels), columns=props)
    grouped = request.GET.get('grouped')
    if grouped == 'kommission':
        data = []
        for gr, df in orig_df.groupby('related_institution__id'):
            item = {}
            item['id'] = gr
            first_row = df.iloc[0]
            item['name'] = first_row['related_institution__name']
            members = {}
            for i, row in df.iterrows():
                member_name = f"{row['related_person__name']}, {row['related_person__first_name']}"
                members[row['related_person__id']] = {
                    'name': member_name,
                    'start_date': f"{row['start_date']}",
                    'end_date': f"{row['end_date']}",
                    'rel_type': row['relation_type__name']
                }
            item['members'] = members
            item['member_amount'] = len(members)
            data.append(item)
    elif grouped == "mitglied":
        data = []
        for gr, df in orig_df.groupby('related_person__id'):
            item = {}
            item['id'] = gr
            first_row = df.iloc[0]
            item['name'] = f"{first_row['related_person__name']}, {first_row['related_person__first_name']}"
            members = {}
            for i, row in df.iterrows():
                member_name = f"{row['related_institution__name']}"
                members[row['related_institution__id']] = {
                    'name': member_name,
                    'start_date': f"{row['start_date']}",
                    'end_date': f"{row['end_date']}",
                    'rel_type': row['relation_type__name']
                }
            item['members'] = members
            item['amount'] = len(members)
            data.append(item)
    else:
        data = orig_df.to_dict('records')
    return JsonResponse(data, safe=False)


def ns_view(request):
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
    result_df = pd.DataFrame(data)

    payload = {
        'title': 'Nationalsozialismus',
        'description': "lorem ipsum",
        'data': result_df.to_dict('records')
    }

    return JsonResponse(payload, safe=False)
