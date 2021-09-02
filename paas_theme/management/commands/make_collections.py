import os
from django.core.management.base import BaseCommand

from apis_core.apis_metainfo.models import Collection
from apis_core.apis_entities.models import Person
from apis_core.apis_relations.models import PersonInstitution
from paas_theme.id_mapping import (
    NSDAP,
    GESAMTAKADEMIE_UND_KLASSEN,
    MITGLIED_AUSWERTUNG_COL_NAME,
    MITGLIED_AUSWERTUNG_NS_COL_NAME,
    NATIONALSOZIALISTEN_COL_NAME,
    RELATION_TYPE_MITGLIEDER_AUSWERTUNG,
    RELATION_TYPE_MITGLIEDER_AUSWERTUNG_NS
)


def get_members(klassen_id=GESAMTAKADEMIE_UND_KLASSEN, rel_types=RELATION_TYPE_MITGLIEDER_AUSWERTUNG):
    """ returns all Persons related to passed in ID"""
    print(klassen_id)
    return list(
        set(
            [x.related_person for x in PersonInstitution.objects.filter(
                related_institution__in=klassen_id,
                relation_type__in=rel_types
            ).distinct()]
        )
    ) 
# for x in [
#     MITGLIED_AUSWERTUNG_COL_NAME,
#     MITGLIED_AUSWERTUNG_NS_COL_NAME,
#     NATIONALSOZIALISTEN_COL_NAME,
# ]:
#     for col in Collection.objects.filter(name__startswith=x):
#         col.delete()



mitglieder_auswertung_collection, _ = Collection.objects.get_or_create(
    name=MITGLIED_AUSWERTUNG_COL_NAME
)

mitglieder_auswertung_ns_collection, _ = Collection.objects.get_or_create(
    name=MITGLIED_AUSWERTUNG_NS_COL_NAME
)
nazi_collection, _ = Collection.objects.get_or_create(
    name=NATIONALSOZIALISTEN_COL_NAME
)

class Command(BaseCommand):
    # Show this when the user types help
    help = "Adds all NSDAP members into dedicated collection"

    # A command must define handle()
    def handle(self, *args, **options):
        for x in get_members(rel_types=RELATION_TYPE_MITGLIEDER_AUSWERTUNG_NS):
            print(
                f"adding <{x}> to collection {mitglieder_auswertung_ns_collection}"
            )
            x.collection.add(mitglieder_auswertung_ns_collection)
        for x in get_members():
            print(
                f"adding <{x}> to collection {mitglieder_auswertung_collection}"
            )
            x.collection.add(mitglieder_auswertung_collection)
        
        mit_ns = Person.objects.filter(collection__name=MITGLIED_AUSWERTUNG_NS_COL_NAME)
        nazis = [
            x.related_person for x in PersonInstitution.objects.filter(
                related_institution__in=NSDAP,
                related_person__in=mit_ns
            )
        ]
        for x in nazis:
            print(
                f"adding <{x}> to collection {nazi_collection}"
            )
            x.collection.add(nazi_collection)
