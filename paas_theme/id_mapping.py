import json

KLASSEN_IDS = [
    2,
    3
]

GESAMTAKADEMIE_UND_KLASSEN = [
    2,
    3,
    500
]

NSDAP = [
    49596,
]

AKADEMIE_KOMMISSION_TYP_ID = 82

MITGLIED_AUSWERTUNG_COL_NAME = 'mitglied_auswertung'
MITGLIED_AUSWERTUNG_NS_COL_NAME = 'mitglied_auswertung_ns'
NATIONALSOZIALISTEN_COL_NAME = 'nationalsozialisten'

with open('./paas_theme/relation_mapping.json') as f:
    rel_mapping = json.load(f)

RELATION_TYPE_MITGLIEDER_AUSWERTUNG = rel_mapping['mitglied_auswertung']
RELATION_TYPE_MITGLIEDER_AUSWERTUNG_NS = rel_mapping['mitglied_auswertung_ns']