import django_tables2 as tables
from django_tables2.utils import A

from apis_core.apis_entities.models import Person
from apis_core.apis_entities.models import Institution

from .provide_data import enrich_person_context

from haystack.models import SearchResult


class PersonTable(tables.Table):

    name = tables.LinkColumn("theme:person-detail", args=[A("id")], verbose_name="Name")

    class Meta:
        model = Person
        sequence = (
            "name",
            "first_name",
        )
        attrs = {"class": "table table-responsive table-hover"}


class InstitutionTable(tables.Table):

    name = tables.LinkColumn(
        "theme:institution-detail", args=[A("id")], verbose_name="Name"
    )

    class Meta:
        model = Institution
        sequence = (
            "name",
            "first_name",
        )
        attrs = {"class": "table table-responsive table-hover"}


class SearchResultTable(tables.Table):

    name = tables.TemplateColumn(
        template_code='<a class="text-oeaw-blau semi-bold" href="/person/{{record.pk}}">{{record.name}}</a>',
        verbose_name="Name",
        attrs={"a": {"class": ".text-oeaw-blau semi-bold"}},
    )

    profession = tables.Column(accessor="profession", verbose_name="Beruf")

    birth_date = tables.DateColumn(
        accessor="birth_date",
        format="Y",
        verbose_name="geboren",
        attrs={"td": {"class": "no-wrap"}},
    )

    death_date = tables.DateColumn(
        accessor="death_date",
        format="Y",
        verbose_name="gestorben",
        attrs={"td": {"class": "no-wrap"}},
    )

    birth_place = tables.Column(accessor="place_of_birth", verbose_name="geboren in")

    # death_place = tables.Column(accessor="place_of_death", verbose_name="gestorben in")

    def render_profession(self, value):
        separator = ", "
        return separator.join(value)

    class Meta:
        model = Person
        fields = (
            "name",
            "birth_date",
            "death_date",
            "birth_place",
            "profession",
        )
        attrs = {"class": "table table-hover custom-table bg-mine", "thead": {}}
        template_name = "theme/custom_table.html"
        row_attrs = {"data-member": lambda record: record.academy_member}


class InstitutionsSearchResultTable(tables.Table):

    # mitgliedschaft = tables.Column(accessor="mitgliedschaft_short", verbose_name="Mgl.")

    name = tables.TemplateColumn(
        template_code='<a class="text-oeaw-blau semi-bold" href="/institution/{{record.pk}}">{{record.name}}</a>',
        verbose_name="Name",
        attrs={"a": {"class": ".text-oeaw-blau semi-bold"}},
    )

    kind = tables.Column(accessor="kind", verbose_name="Typ")

    start_date = tables.DateColumn(
        accessor="start_date",
        format="d. m. Y",
        verbose_name="von",
        attrs={"td": {"class": "no-wrap"}},
    )

    end_date = tables.DateColumn(
        accessor="end_date",
        format="d. m. Y",
        verbose_name="bis",
        attrs={"td": {"class": "no-wrap"}},
    )

    def render_profession(self, value):
        separator = ", "
        return separator.join(value)

    class Meta:
        model = Institution
        fields = (
            "name",
            "start_date",
            "end_date",
            "kind",
        )
        attrs = {"class": "table table-hover custom-table bg-mine", "thead": {}}
        template_name = "theme/custom_table.html"
        row_attrs = {"data-member": lambda record: record.academy_member}
