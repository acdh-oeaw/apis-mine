import datetime
import pandas as pd

from django.http import JsonResponse

from apis_core.apis_relations.models import PersonInstitution, PersonPerson
from . id_mapping import NSDAP, KLASSEN_IDS
from . provide_data import NATIONALSOZIALISTEN, KOMMISSIONEN, get_child_classes, PersonPersonRelation

from . analyze_utils import get_ns, nazi_komm_df

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


def proposed_by_nazi(request):
    pers_pers = PersonPerson.objects.filter(
        relation_type__in=get_child_classes([3141], PersonPersonRelation),
        related_personB_id__in=NATIONALSOZIALISTEN
    ).values_list(*person_person_props)
    orig_df = pd.DataFrame(pers_pers, columns=person_person_props)
    data = orig_df.to_dict('records')
    return JsonResponse(data, safe=False)


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
    orig_df = nazi_komm_df()
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
    result_df = pd.DataFrame(get_ns())

    payload = {
        'title': 'Nationalsozialismus',
        'description': "lorem ipsum",
        'data': result_df.to_dict('records')
    }

    return JsonResponse(payload, safe=False)
