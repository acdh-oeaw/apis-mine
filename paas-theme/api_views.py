from rest_framework.generics import ListAPIView
from haystack.query import SearchQuerySet
from .forms import PersonFacetedSearchForm
from apis_core.api_routers import serializers_dict
from apis_core.apis_relations.models import PersonInstitution
from apis_core.api_renderers import NetJsonRenderer
from django.conf import settings


class NetVizTheme(ListAPIView):
    action = "list"
    renderer_classes = [NetJsonRenderer]

    def get_serializer_class(self):
        return serializers_dict["PersoninstitutionSerializer"]

    def get_queryset(self):
        kwargs = {"load_all": True, "searchqueryset": SearchQuerySet()}
        qs_d = self.request.GET.copy()
        network = qs_d.pop("network_type")
        sqs1 = PersonFacetedSearchForm(qs_d, **kwargs).search()
        pi = PersonInstitution.objects.filter(
            related_person_id__in=[x.pk for x in sqs1]
        )
        if "kommissionen" in network:
            rel_names = getattr(settings, "APIS_SEARCH_COMISSIONS", [])
            pi = pi.filter(relation_type__name__in=rel_names)
        elif "universitaeten" in network:
            pi = pi.filter(related_institution__kind__name="Universität")
        elif "andere_akademien" in network:
            pi = pi.filter(related_institution__kind__name="Akademie (Ausland)")
        elif "ausbildung" in network:
            rel_names = getattr(settings, "APIS_SEARCH_EDUCATION", [])
            pi = pi.filter(relation_type__name__in=rel_names)
        elif "karierre" in network:
            rel_names = getattr(settings, "APIS_SEARCH_CAREER", [])
            pi = pi.filter(relation_type__name__in=rel_names)
        return pi
