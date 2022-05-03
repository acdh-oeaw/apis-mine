import json

KLASSEN_IDS = [
    2,
    3
]

GESAMTAKADEMIE_UND_KLASSEN = KLASSEN_IDS + [
    1,
    500,
    59131,
    501
] # added Junge Kurie und junge Akademie

MITGLIEDSCHAFT = [
    4179, # Mitglied >> Ehrenmitglied (EM) >> gewählt und bestätigt
    4175, # Mitglied >> Ehrenmitglied (EM) >> gewählt und ernannt
    50, # Mitglied >> Ehrenmitglied (EM) >> Bestätigt
    45, # Mitglied >> Ehrenmitglied (EM) >> Ernannt
    40, # Mitglied >> Ehrenmitglied (EM) >> Genehmigt
    34, # Mitglied >> Ehrenmitglied (EM) >> Gewählt
    4180, # Mitglied >> Wirkliches Mitglied (wM) >> gewählt und bestätigt
    4174, # Mitglied >> Wirkliches Mitglied (wM) >> gewählt und ernannt
    3459, # Mitglied >> Wirkliches Mitglied (wM) >> reaktiviert
    129, # Mitglied >> Wirkliches Mitglied (wM) >> eingereiht
    56, # Mitglied >> Wirkliches Mitglied (wM) >> Umgewidmet
    46, # Mitglied >> Wirkliches Mitglied (wM) >> Ernannt
    33, # Mitglied >> Wirkliches Mitglied (wM) >> Gewählt
    4177, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> gewählt und bestätigt
    3471, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> reaktiviert
    130, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> eingereiht
    57, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> Umgewidmet
    52, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> Bestätigt
    47, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> Ernannt
    42, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> Genehmigt
    35, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> Gewählt
    4176, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> gewählt und bestätigt
    3460, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> reaktiviert
    131, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> eingereiht
    58, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> Umgewidmet
    53, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> Bestätigt
    48, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> Ernannt
    43, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> Genehmigt
    36, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> Gewählt
    19, # Mitglied >> Mitglied der Jungen Kurie,
    59, # Mitglied >> Ordentliches Mitglied (oM) >> Umgewidmet
    54 # Mitglied >> Ordentliches Mitglied (oM) >> gewählt und bestätigt
]

NSDAP = [
    49596,
]

RUHEND_GESTELLT = [
    3373, # Mitglied >> Korrespondierendes Mitglied im Ausland (kM A) >> ruhend gestellt
    3374, # Mitglied >> Mitglied der Jungen Kurie >> ruhend gestellt
    3456, # Mitglied >> Wirkliches Mitglied (wM) >> ruhend gestellt
    3457, # Mitglied >> Korrespondierendes Mitglied im Inland (kM I) >> ruhend gestellt
]

AKADEMIE_KOMMISSION_TYP_ID = 82

MITGLIED_AUSWERTUNG_COL_NAME = 'mitglied_auswertung'
MITGLIED_AUSWERTUNG_NS_COL_NAME = 'mitglied_auswertung_ns'
NATIONALSOZIALISTEN_COL_NAME = 'nationalsozialisten'

with open('./paas_theme/relation_mapping.json') as f:
    rel_mapping = json.load(f)

RELATION_TYPE_MITGLIEDER_AUSWERTUNG = rel_mapping['mitglied_auswertung']
RELATION_TYPE_MITGLIEDER_AUSWERTUNG_NS = rel_mapping['mitglied_auswertung_ns']

NOBEL_PREISE = [45721, 44859, 51502, 60045, 60049, 60062, 60072]

RELATION_PREISTRAEGER = [138]

RELATION_GEBURTSORT = [3090, 152, 64]

GELEGEN_IN = [69]

INSTITUTION_TYPE_AKADEMIE = [
    4309,   # Beirat
    4302,   # Kuratorium
    4301,   # Komitee
    4236,   # Einrichtung
    4235,   # Forschungsorientierte Einheit
    98,     # Institution der Gesamtakademie
    85,     # Klasse
    84,     # Forschungsstelle
    83,     # Institut
    82,     # Kommission
    81      # Akademie
    ]

INSTITUTION_MEMBERS_TYPES = {
    'president': [88, 162, 97, 96, 95, 94],
    'members': [26, 164]
}

INSTITUTION_STRUCTURE_IDS = [
    2, 
    99,
    4203        # gliedert ein
    ]

INSTITUTION_HISTORY_IDS = {
    "Institutionelle Vorläufer": [
        4205, 
        161,    # preceeding
        7,      # ist Nachfolger von
        6       # umbenannt von
        ],
    "Institutionelle Nachfolger": [
        4214,   # gründet neu
        4204,   # übertragen an
        4202,   # umgewandelt in
        160,    # succeeding
        5,      # ist Vorgänger von
        4,      # zusammengelegt mit
        3       # umbenannt in
        ]
}

INSTITUTION_TYPE_MEMBERSHIP = {
    "OBFRAUEN / OBMÄNNER": [
        162,    # Stellvertreter Kommission
        30,     # Obmann Kommission
        97,     # Kuratorium Stellvertreter
        96,     # Advisory Board Stellvertreter
        95,     # Kuratorium Obmann
        94,     # Advisory Board Obmann
        30      # Kommission Obmann 
        ],
    "DIREKTORINEN / DIREKTOREN": [
        88      # Direktor Institut
    ],
    "MITGLIEDER": [
        26      # Kommissionsmitglied
    ]
}