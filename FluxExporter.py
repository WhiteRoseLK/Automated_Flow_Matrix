#!/usr/bin/env python3
"""
Exporteur de flux réseau vers des fichiers YAML Ansible-friendly

Ce script :
1. Lit le fichier flows_populated.csv contenant les flux enrichis
2. Groupe les flux par machine source
3. Génère un fichier YAML par machine source dans YAML_Output/
4. Formate les fichiers pour être compatibles avec Ansible

Utilisé pour :
- Générer des playbooks Ansible par machine
- Créer des configurations de firewall automatisées
- Faciliter le déploiement des règles réseau

Prérequis :
- flows_populated.csv : Fichier de flux enrichi par DataPopulation.py
"""

import csv
import pandas as pd
import ipaddress
import yaml
from collections import defaultdict
import os

# ------------------------------
# CONFIGURATION
# ------------------------------
INPUT_DIR = "Input"
CSV_FILE = 'flows_populated.csv'
CSV_PATH = f"{INPUT_DIR}/{CSV_FILE}"
OUTPUT_DIR = 'YAML_Output'
flux_par_source = defaultdict(list)

# ------------------------------
# CONFIGURATION DES COLONNES
# ------------------------------
# Colonnes à exporter dans les fichiers YAML
filter_columns = [
    'source_name', 'source_ip', 'destination_name', 'destination_ip', 'port', 'protocol', 'description'
]

# ------------------------------
# CLASSES UTILITAIRES
# ------------------------------
class IndentDumper(yaml.Dumper):
    """
    Dumper YAML personnalisé pour un formatage propre compatible Ansible
    """
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

# ------------------------------
# TRAITEMENT PRINCIPAL
# ------------------------------
if __name__ == "__main__":
    print("📤 Exporteur de flux vers YAML Ansible")
    print("=" * 50)
    
    # Chargement des données
    print(f"📈 Chargement de {CSV_PATH}...")
    try:
        df_csv = pd.read_csv(CSV_PATH)
        print(f"✅ {len(df_csv)} flux chargés")
    except FileNotFoundError:
        print(f"❌ Erreur: {CSV_PATH} introuvable")
        print("   Exécutez d'abord DataPopulation.py")
        exit(1)
    
    # Filtrage des colonnes nécessaires
    print(f"🔍 Filtrage des colonnes : {', '.join(filter_columns)}")
    df_filtered = df_csv.filter(items=filter_columns).sort_values(by=['source_name'])
    
    # Création du répertoire de sortie
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Répertoire créé : {OUTPUT_DIR}")
    
    # Groupement par source et génération des fichiers YAML
    print("\n🔄 Génération des fichiers YAML par machine source...")
    files_created = 0
    
    for source_name, group in df_filtered.groupby('source_name'):
        flux_list = group.to_dict(orient='records')
        filename = f"{OUTPUT_DIR}/{source_name}.yml"
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(
                {'flows': flux_list},
                f,
                Dumper=IndentDumper,
                sort_keys=False,
                default_flow_style=False,
                indent=2
            )
        
        print(f"  ✅ {filename} ({len(flux_list)} flux)")
        files_created += 1
    
    print(f"\n✅ Export terminé avec succès !")
    print(f"  • {files_created} fichiers YAML créés")
    print(f"  • {len(df_filtered)} flux exportés")
    print(f"  • Répertoire : {OUTPUT_DIR}/")

