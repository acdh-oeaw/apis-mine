import django_tables2 as tables
from django_tables2.utils import A

from apis_core.apis_entities.models import Person

from .utils import enrich_person_context

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


class SearchResultTable(tables.Table):

    wm = tables.TemplateColumn(
        template_code='{% if record.academy_member %}<i data-feather="check-circle"></i>{% else %}<i data-feather="circle"></i>{% endif %}'
    )

    name = tables.TemplateColumn(
        template_code='<a class="oebl-font-red semi-bold" href="person/{{record.pk}}?mapview=true">{{record.name}}</a>',
        verbose_name="Name",
        attrs={"a": {"class": "oebl-font-red semi-bold"}},
    )

    profession = tables.Column(accessor="profession", verbose_name="Beruf")

    birth_date = tables.DateColumn(
        accessor="birth_date",
        format="d. m. Y",
        verbose_name="geboren am",
        attrs={"td": {"class": "no-wrap"}},
    )

    death_date = tables.DateColumn(
        accessor="death_date",
        format="d. m. Y",
        verbose_name="gestorben am",
        attrs={"td": {"class": "no-wrap"}},
    )

    birth_place = tables.Column(accessor="place_of_birth", verbose_name="geboren in")

    death_place = tables.Column(accessor="place_of_death", verbose_name="gestorben in")

    def render_profession(self, value):
        separator = ", "
        return separator.join(value)

    class Meta:
        model = Person
        fields = (
            "wm",
            "name",
            "birth_date",
            "birth_place",
            "death_date",
            "death_place",
            "profession",
        )
        attrs = {"class": "table table-hover oebl-table", "thead": {}}
        template_name = "theme/custom_table.html"
        row_attrs = {"data-member": lambda record: record.academy_member}
