#!/usr/bin/env python3
"""
Gestionnaire de matrice de flux réseau avec versioning

Ce script :
1. Lit le fichier flows.csv pour obtenir les nouveaux flux
2. Charge la dernière version de la matrice Excel existante
3. Met à jour la matrice avec les nouveaux flux
4. Gère le versioning automatique (Matrix_vX.Y.xlsx)
5. Ajoute les informations de zone basées sur les adresses IP
6. Maintient une règle "block all" en fin de matrice

Fonctionnalités :
- Versioning automatique des matrices
- Mise à jour incrémentale des flux
- Enrichissement avec zones réseau
- Gestion des actions (ajout/suppression)
- Export Excel automatisé

Prérequis :
- flows.csv : Fichier source des flux réseau
- cmdb_network.csv : Table de correspondance IP/Zone
- Flow_Matrix/ : Répertoire des matrices Excel
"""

import pandas as pd
import os
import re
import ipaddress

# ------------------------------
# CONFIGURATION
# ------------------------------
CSV_FILE = "flows.csv"
SUBNET_FILE = "cmdb_network.csv"
INPUT_DIR = "Input"
CSV_PATH = f"{INPUT_DIR}/{CSV_FILE}"
SUBNET_PATH = f"{INPUT_DIR}/{SUBNET_FILE}"
EXCEL_FILE_PATTERN = r"Matrix_v(\d+)\.(\d+)\.xlsx"
OUTPUT_DIR = "Flow_Matrix"
OUTPUT_PREFIX = "Matrix_v"
OUTPUT_SUFFIX = ".xlsx"

KEY_COLUMNS = ['source', 'destination', 'port', 'protocol']

# ------------------------------
# FONCTIONS UTILITAIRES
# ------------------------------

def get_latest_matrix():
    """
    Trouve la dernière version de la matrice Excel basée sur le numéro de version
    
    Returns:
        str: Chemin vers la dernière matrice ou None si aucune trouvée
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        return None
        
    files = [f for f in os.listdir(OUTPUT_DIR) if re.match(EXCEL_FILE_PATTERN, f)]
    if not files:
        return None
        
    def version_key(f):
        m = re.match(EXCEL_FILE_PATTERN, f)
        return int(m.group(1)), int(m.group(2))
        
    files.sort(key=version_key, reverse=True)
    return f"{OUTPUT_DIR}/{files[0]}"

def next_version(filename):
    """
    Calcule la version suivante pour une matrice
    
    Args:
        filename (str): Chemin de la matrice actuelle
        
    Returns:
        str: Nom de fichier de la prochaine version
    """
    match = re.match(f"{OUTPUT_DIR}/{EXCEL_FILE_PATTERN}", filename)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2)) + 1
        return f"{OUTPUT_PREFIX}{major}.{minor}{OUTPUT_SUFFIX}"
    else:
        return f"{OUTPUT_PREFIX}1.0{OUTPUT_SUFFIX}"

def ip_to_zone(ip, subnet_df):
    """
    Trouve la zone correspondante à une adresse IP
    
    Args:
        ip (str): Adresse IP à analyser
        subnet_df (DataFrame): DataFrame des correspondances réseau/zone
        
    Returns:
        str: Nom de la zone ou None si non trouvée
    """
    try:
        ip_addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
        
    for _, row in subnet_df.iterrows():
        network = ipaddress.ip_network(row['sous-reseau'])
        if ip_addr in network:
            return row['zone']
    return None

def insert_column_after(df, new_col_name, new_col_values, after_col):
    """
    Insère une nouvelle colonne après une colonne spécifiée
    
    Args:
        df (DataFrame): DataFrame à modifier
        new_col_name (str): Nom de la nouvelle colonne
        new_col_values: Valeurs de la nouvelle colonne
        after_col (str): Nom de la colonne après laquelle insérer
        
    Returns:
        DataFrame: DataFrame modifié
    """
    idx = df.columns.get_loc(after_col) + 1
    df.insert(idx, new_col_name, new_col_values)
    return df

# ------------------------------
# TRAITEMENT PRINCIPAL
# ------------------------------

if __name__ == "__main__":
    print("📈 Gestionnaire de matrice de flux avec versioning")
    print("=" * 50)
    
    # Vérification des fichiers requis
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"❌ Le fichier CSV {CSV_PATH} n'existe pas.")
    if not os.path.exists(SUBNET_PATH):
        raise FileNotFoundError(f"❌ Le fichier de correspondance {SUBNET_PATH} n'existe pas.")
    
    # Chargement des données
    print(f"📈 Chargement de {CSV_PATH}...")
    df_csv = pd.read_csv(CSV_PATH)
    print(f"✅ {len(df_csv)} flux chargés")
    
    print(f"🗂 Chargement de {SUBNET_PATH}...")
    df_subnets = pd.read_csv(SUBNET_PATH)
    print(f"✅ {len(df_subnets)} correspondances réseau chargées")

# ------------------------------
# Compléter zone_source et zone_destination
# ------------------------------
zone_source = df_csv['source'].apply(lambda ip: ip_to_zone(ip, df_subnets))
zone_destination = df_csv['destination'].apply(lambda ip: ip_to_zone(ip, df_subnets))

df_csv = insert_column_after(df_csv, 'zone_source', zone_source, 'source')
df_csv = insert_column_after(df_csv, 'zone_destination', zone_destination, 'destination')

# ------------------------------
# Lecture matrice Excel existante
# ------------------------------
last_excel = get_latest_matrix()
if last_excel:
    df_excel = pd.read_excel(last_excel)
    new_excel_name = f"{OUTPUT_DIR}/{next_version(last_excel)}"
else:
    df_excel = pd.DataFrame(columns=df_csv.columns)
    new_excel_name = f"{OUTPUT_DIR}/{OUTPUT_PREFIX}1.0{OUTPUT_SUFFIX}"

# ------------------------------
# Mise à jour de la matrice
# ------------------------------
df_excel.set_index(KEY_COLUMNS, inplace=True, drop=False)
df_csv.set_index(KEY_COLUMNS, inplace=False)

# Mettre à jour les flux existants
df_excel.update(df_csv)

# Ajouter les nouveaux flux
new_rows = df_csv[~df_csv.set_index(KEY_COLUMNS).index.isin(df_excel.index)]
df_updated = pd.concat([df_excel, new_rows])

# Supprimer les flux marqués "supprimer" si action existe
if 'action' in df_csv.columns:
    to_remove = df_csv[df_csv['action'].str.lower() == 'supprimer']
    df_updated = df_updated[~df_updated.set_index(KEY_COLUMNS).index.isin(to_remove.set_index(KEY_COLUMNS).index)]

df_updated.reset_index(drop=True, inplace=True)

# ------------------------------
# Ajouter ou remplacer la colonne ID en début
# ------------------------------
if 'ID' in df_updated.columns:
    df_updated.drop(columns=['ID'], inplace=True)
df_updated.insert(0, 'ID', range(1, len(df_updated) + 1))  # ID incrémental

# ------------------------------
# Placer la colonne action en 2ème position
# ------------------------------
if 'action' in df_updated.columns:
    action_col = df_updated.pop('action')
    df_updated.insert(1, 'action', action_col)

# ------------------------------
# Supprimer l'ancienne ligne "block all" si elle existe
# ------------------------------
if 'action' in df_updated.columns and 'source' in df_updated.columns and 'destination' in df_updated.columns:
    df_updated = df_updated[~((df_updated['action'].str.lower() == 'block') &
                              (df_updated['source'] == 'any') &
                              (df_updated['destination'] == 'any'))]

# ------------------------------
# Ajouter la dernière règle "block all"
# ------------------------------
block_all_rule = {col: '' for col in df_updated.columns}
block_all_rule['source'] = 'any'
block_all_rule['destination'] = 'any'
block_all_rule['port'] = 'any'
block_all_rule['protocol'] = 'any'
block_all_rule['action'] = 'block'
block_all_rule['ID'] = len(df_updated) + 1
if 'zone_source' in df_updated.columns:
    block_all_rule['zone_source'] = 'any'
if 'zone_destination' in df_updated.columns:
    block_all_rule['zone_destination'] = 'any'

df_updated = pd.concat([df_updated, pd.DataFrame([block_all_rule])], ignore_index=True)

# ------------------------------
# Réorganiser les colonnes pour garder l'ordre exact
# ------------------------------
cols = df_updated.columns.tolist()
# ID en 1ère position
if 'ID' in cols:
    cols.insert(0, cols.pop(cols.index('ID')))
# action en 2ème position
if 'action' in cols:
    cols.insert(1, cols.pop(cols.index('action')))
# zone_source après source
if 'source' in cols and 'zone_source' in cols:
    idx_source = cols.index('source')
    cols.insert(idx_source + 1, cols.pop(cols.index('zone_source')))
# zone_destination après destination
if 'destination' in cols and 'zone_destination' in cols:
    idx_dest = cols.index('destination')
    cols.insert(idx_dest + 1, cols.pop(cols.index('zone_destination')))
df_updated = df_updated[cols]

# ------------------------------
# Export Excel mis à jour
# ------------------------------
df_updated.to_excel(new_excel_name, index=False)
print(f"Matrice mise à jour et enregistrée dans : {new_excel_name}")
