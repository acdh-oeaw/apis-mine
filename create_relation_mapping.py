import json
import pandas as pd
df = pd.read_csv('relation_types_csv.csv')

relation_mapping = {}
for key in df.keys():
    if 'auswertung' in key:
        query = f'{key}=="J" and relation_type=="Person-Institution-Relation"'
        relation_mapping[key] = sorted(df.query(query)['primary_key'].to_list())
        
with open('./paas_theme/relation_mapping.json', 'w') as f:
    f.write(json.dumps(relation_mapping, indent=4))