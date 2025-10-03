import csv
import yaml
from collections import defaultdict

file_direcotry = "Input"
csv_file = 'flows.csv'
csv_path = f"{file_direcotry}/{csv_file}"
output_dir = 'YAML_Output'
flux_par_source = defaultdict(list)

# Lecture du CSV
with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        flux_par_source[row['source']].append({
            'destination': row['destination'],
            'port': int(row['port']),
            'protocol': row['protocol'],
            'description': row['description']
        })

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

# Génération des fichiers YAML Ansible-friendly
for source, flux_list in flux_par_source.items():
    filename = f"{output_dir}/{source}.yml"
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
