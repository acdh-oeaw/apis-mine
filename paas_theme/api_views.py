from typing import List
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from haystack.query import SearchQuerySet
from .forms import PersonFacetedSearchFormNew
from apis_core.api_routers import serializers_dict
from apis_core.apis_relations.models import PersonInstitution, PersonPlace
from apis_core.apis_entities.models import Institution, Person
from apis_core.api_renderers import NetJsonRenderer
from django.conf import settings
from copy import deepcopy
from django.db.models import Q
from .filters import KommissionenFilter
from .serializers_analyse import KommissionZeitstrahl, KommissionenZeitstrahlNazis
from apis_core.apis_entities.serializers import LifePathSerializer

from .provide_data import classes

relation_type_dict = {
    "personinstitution": PersonInstitution,
    "personplace": PersonPlace,
}

class GetKommissionen(ListAPIView):
    action = "list"
    filterset_class = KommissionenFilter
    queryset = Institution.objects.filter(kind_id=82)

    def get_serializer_class(self):
        #qs_d = self.request.GET.copy()
        if "count_nazis" in self.request.query_params.keys():
            return KommissionenZeitstrahlNazis
        else:
            return KommissionZeitstrahl




class NetVizTheme(ListAPIView):
    action = "list"
    renderer_classes = [NetJsonRenderer]

    def get_serializer_class(self):
        return serializers_dict[
            f"{self._relation_type[0]+self._relation_type[1:].lower()}Serializer"
        ]

    def get_queryset(self):
        kwargs = {"load_all": True, "searchqueryset": SearchQuerySet()}
        qs_d = self.request.GET.copy()
        network = qs_d.pop("network_type")
        query_dict = deepcopy(classes["netzwerk"][network[0]])
        self._relation_type = query_dict["relation"]
        sqs1 = PersonFacetedSearchFormNew(qs_d, **kwargs).search()
        pi = relation_type_dict[query_dict["relation"].lower()].objects.filter(
            related_person_id__in=[x.pk for x in sqs1]
        )
        if "relation" in query_dict.keys():
            del query_dict["relation"]
        if "label" in query_dict.keys():
            del query_dict["label"]
        pi = pi.filter(**query_dict)
        return pi


class EgoNetwork(APIView):
    renderer_classes = [NetJsonRenderer]

    def get(self, request, format=None):
        pk = request.query_params["pk"]
        level = request.query_params.get("level", 1)
        rel_types = []
        for c in classes["akad_funktionen"]:
            rel_types.extend(classes["akad_funktionen"][c][0])
        pi1 = PersonInstitution.objects.filter(
            related_institution__kind_id__in=[82],
            relation_type_id__in=rel_types,
            related_person_id=pk,
            start_date__isnull=False,
            end_date__isnull=False,
        )
        res = {"results": []}

        if pi1.count() > 0:
            data1 = serializers_dict["PersoninstitutionSerializer"](
                pi1,
                many=True,
                context={"request": request, "view": self.schema.view},
            )
            res["results"].extend(data1.data)
        i1 = [(p.related_institution, p.start_date, p.end_date) for p in pi1]
        rel_insts = i1
        while level > 0:
            condition = Q()
            for ii in i1:
                condition.add(
                    Q(
                        related_institution=ii[0],
                        start_date__lte=ii[2],
                        end_date__gte=ii[1],
                        relation_type_id__in=rel_types,
                    ),
                    Q.OR,
                )
            if len(i1) == 0:
                break
            pi2 = PersonInstitution.objects.filter(condition).exclude(
                related_person_id=pk
            )
            if pi2.count() > 0:
                res["results"].extend(
                    serializers_dict["PersoninstitutionSerializer"](
                        pi2,
                        many=True,
                        context={"request": request, "view": self.schema.view},
                    ).data
                )
            level -= 1
            if level > 0:
                i1 = [
                    i.related_institution
                    for i in pi.exclude(related_institution__in=rel_insts)
                ]
                rel_insts.extend(i1)
        return Response(res)


class LifePathMINEViewset(APIView):
    def get(self, request, pk):
        b_rel = [3090, 152, 64]
        d_rel = [3054, 153, 3091]
        pb_pd = b_rel + d_rel
        lst_inst = list(
            PersonInstitution.objects.filter(
                Q(related_person_id=pk),
                Q(start_date__isnull=False) | Q(end_date__isnull=False),
                Q(relation_type_id__in=classes["berufslaufbahn_ids"] + [
                    1369, # absolvierte Studim an
                    176 # schloss Schule ab
                ]),
            ).filter_for_user()
        )
        lst_place = list(
            PersonPlace.objects.filter(
                Q(related_person_id=pk),
                Q(start_date__isnull=False)
                | Q(end_date__isnull=False)
                | Q(relation_type_id__in=pb_pd),
            ).filter_for_user()
        )
        comb_lst = lst_inst + lst_place
        p1 = Person.objects.get(pk=pk)
        if p1.start_date:
            for e in comb_lst:
                if e.relation_type_id in b_rel:
                    e.start_date = p1.start_date
        if p1.end_date:
            for e in comb_lst:
                if e.relation_type_id in d_rel:
                    e.start_date = p1.end_date
        data = LifePathSerializer(comb_lst, many=True).data
        data = [d for d in data if d is not None]
        data = sorted(data, key=lambda i: i["year"])

        return Response(data)