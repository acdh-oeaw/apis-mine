from rest_framework.generics import ListAPIView
from haystack.query import SearchQuerySet
from .forms import PersonFacetedSearchFormNew
from apis_core.api_routers import serializers_dict
from apis_core.apis_relations.models import PersonInstitution, PersonPlace
from apis_core.api_renderers import NetJsonRenderer
from django.conf import settings
from copy import deepcopy

from .provide_data import classes

relation_type_dict = {
    "personinstitution": PersonInstitution,
    "personplace": PersonPlace,
}


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
