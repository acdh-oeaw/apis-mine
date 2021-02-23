import itertools

from dal import autocomplete
from django.db.models import Q

from apis_core.apis_labels.models import Label
from apis_core.apis_vocabularies.models import ProfessionType
from .utils import oebl_persons


class ProfessionAC(autocomplete.Select2QuerySetView):

    def get_result_label(self, item):
        return f"{item.name}"

    def get_queryset(self):
        if self.q:
            query = self.q
            match = ProfessionType.objects.filter(
                name__icontains=query
            )
            return match
        else:
            return []


class OeblPersons(autocomplete.Select2QuerySetView):

    def get_result_label(self, item):
        labels = "; ".join([x.label for x in item.label_set.all()])
        return f"{item.name}, {item.first_name} ({item.start_date} - {item.end_date}; {labels})"

    def get_queryset(self):
        if self.q:
            query = self.q
            label_match = list(
                [
                    x.temp_entity.get_child_entity() for x in Label.objects.filter(
                        temp_entity__in=oebl_persons
                    ).filter(label__icontains=query)
                ]
            )
            match = oebl_persons.filter(
                Q(name__icontains=query) |
                Q(first_name__icontains=query)
            )
            all_matches = list(set(itertools.chain(*[match, label_match])))
            return all_matches
        else:
            return []
