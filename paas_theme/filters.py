import django_filters
from dal import autocomplete

from apis_core.apis_entities.models import Person, Institution
from apis_core.apis_relations.models import PersonInstitution
from apis_core.apis_vocabularies.models import ProfessionType
from .filter_utils import born_in_filter, died_in_filter
from .provide_data import get_born_range, get_died_range, NATIONALSOZIALISTEN
from .widgets import NoUISliderInput

born_range = get_born_range()
died_range = get_died_range()


class KommissionenFilter(django_filters.FilterSet):
    aktiv_bis = django_filters.DateFilter(field_name="end_date", lookup_expr="lte")
    aktiv_von = django_filters.DateFilter(field_name="start_date", lookup_expr="gte")
    ns_mitglieder = django_filters.BooleanFilter(method="ns_mitglieder_filter")

    def ns_mitglieder_filter(self, queryset, name, value):
        if value:
            kom_nazi = PersonInstitution.objects.filter(related_person__in=NATIONALSOZIALISTEN, related_institution__in=queryset).values_list("related_institution_id", flat=True)
            return queryset.filter(id__in=list(kom_nazi))
        else:
            return queryset

    class Meta:
        model = Institution
        exclude = ["annotation_set_relation"]
     


class PersonListFilter(django_filters.FilterSet):
    place_of_birth = django_filters.CharFilter(
        lookup_expr="icontains",
        field_name="related_place__name",
        method=born_in_filter,
        label="Geburtsort",
        help_text="Zeichenkette die Namen des Geburtsortes enthalten sein sollte",
    )
    place_of_death = django_filters.CharFilter(
        lookup_expr="icontains",
        field_name="related_place__name",
        method=died_in_filter,
        label="Sterbeort",
        help_text="Zeichenkette die Namen des Sterbeortes enthalten sein sollte",
    )
    id = django_filters.NumberFilter(
        label="Name",
        widget=autocomplete.ListSelect2(
            url="theme:obel-person-autocomplete",
            attrs={
                "data-placeholder": "Suche...",
                "data-minimum-input-length": 3,
            },
        ),
    )
    profession = django_filters.ModelMultipleChoiceFilter(
        label="Berufe",
        queryset=ProfessionType.objects.all(),
        help_text="Berufe und Berufsgruppen (autocomplete)",
        widget=autocomplete.Select2Multiple(
            url="theme:obel-professions-autocomplete",
            attrs={
                "data-placeholder": "Unterrichtswesen...",
                "data-minimum-input-length": 3,
            },
        ),
    )
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Nachname",
        help_text="Zeichenkette die im Nachnamen enthalten sein muss",
    )
    first_name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Vorname",
        help_text="Zeichenkette die im Vornamen enthalten sein muss",
    )

    start_date = django_filters.DateFromToRangeFilter(
        label="Geburtsdatum (Zeitraum)",
        widget=NoUISliderInput(
            attrs={
                "date_min": born_range[0].strftime("%Y-%m-%d"),
                "date_max": born_range[1].strftime("%Y-%m-%d"),
            }
        ),
    )

    end_date = django_filters.DateFromToRangeFilter(
        label="Sterbedatum (Zeitraum)",
        widget=NoUISliderInput(
            attrs={
                "date_min": died_range[0].strftime("%Y-%m-%d"),
                "date_max": died_range[1].strftime("%Y-%m-%d"),
            }
        ),
    )

    class Meta:
        model = Person
        exclude = ["annotation_set_relation"]
