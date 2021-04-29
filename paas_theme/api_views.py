from rest_framework.generics import ListAPIView
from haystack.query import SearchQuerySet
from .forms import PersonFacetedSearchFormNew
from apis_core.api_routers import serializers_dict
from apis_core.apis_relations.models import PersonInstitution
from apis_core.api_renderers import NetJsonRenderer
from django.conf import settings

from .provide_data import classes


class NetVizTheme(ListAPIView):
    action = "list"
    renderer_classes = [NetJsonRenderer]

    def get_serializer_class(self):
        return serializers_dict["PersoninstitutionSerializer"]

    def get_queryset(self):
        kwargs = {"load_all": True, "searchqueryset": SearchQuerySet()}
        qs_d = self.request.GET.copy()
        network = qs_d.pop("network_type")
        sqs1 = PersonFacetedSearchFormNew(qs_d, **kwargs).search()
        pi = PersonInstitution.objects.filter(
            related_person_id__in=[x.pk for x in sqs1]
        )
        query_dict = classes["netzwerk"][network[0]]
        if "label" in query_dict.keys():
            del query_dict["label"]
        pi = pi.filter(**query_dict)
        return pi
