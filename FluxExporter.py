import csv
import pandas as pd
import ipaddress
import yaml
from collections import defaultdict

INPUT_DIR = "Input"
CSV_FILE = 'flows_populated.csv'
CSV_PATH = f"{INPUT_DIR}/{CSV_FILE}"
OUTPUT_DIR = 'YAML_Output'
flux_par_source = defaultdict(list)

filter_columns = [
    'source_name', 'source_ip', 'destination_name', 'destination_ip', 'port', 'protocol', 'description'
]

df_csv = pd.read_csv(CSV_PATH)
df_filtered = df_csv.filter(items=filter_columns).sort_values(by=['source_name'])

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

# Génération des fichiers YAML Ansible-friendly
for flux_list in df_filtered.groupby('source_name')[filter_columns].apply(lambda x: x.to_dict(orient='records')):
    filename = f"{OUTPUT_DIR}/{flux_list[0]['source_name']}.yml"
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(
            {'flows': flux_list},
            f,
            Dumper=IndentDumper,
            sort_keys=False,
            default_flow_style=False,
            indent=2
        )
    print(f"Fichier créé : {filename}")

