# Auto Devops Test APIS


## scripts and configs

* `create_relation_mapping` -> parses `relation_types_csv.csv` (a csv copy of [Relation Excel](https://oeawacat.sharepoint.com/:x:/r/sites/ACDH-CH_p_ProsopographyOfTheMembersOfTheAcademyOfSciences_PA/Shared%20Documents/General/Relationtypes_12.3..xlsx?d=w1d36c92eeed14cfba9277e17dcfe6159&csf=1&web=1&e=0CrMaA)) and writes `paas_them/relation_mapping.json`

* `paas_them/relation_mapping.json` is parsed by `id_mapping.py` which provides useful constants for the application
