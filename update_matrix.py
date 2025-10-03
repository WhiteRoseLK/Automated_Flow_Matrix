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
- Gestion des actions (ajout/suppression)
- Export Excel automatisé

Prérequis :
- flows.csv : Fichier source des flux réseau
- Flow_Matrix/ : Répertoire des matrices Excel
"""

import os
import re
import pandas as pd

# ------------------------------
# CONFIGURATION
# ------------------------------
CSV_FILE = "flows.csv"
INPUT_DIR = "Input"
CSV_PATH = f"{INPUT_DIR}/{CSV_FILE}"
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
    return f"{OUTPUT_PREFIX}1.0{OUTPUT_SUFFIX}"

# ------------------------------
# TRAITEMENT PRINCIPAL
# ------------------------------

if __name__ == "__main__":
    print("📈 Gestionnaire de matrice de flux avec versioning")
    print("=" * 50)

    # Vérification des fichiers requis
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"❌ Le fichier CSV {CSV_PATH} n'existe pas.")

    # Chargement des données
    print(f"📈 Chargement de {CSV_PATH}...")
    df_csv = pd.read_csv(CSV_PATH)
    print(f"✅ {len(df_csv)} flux chargés")

# ------------------------------
# Lecture matrice Excel existante
# ------------------------------
last_excel = get_latest_matrix()
if last_excel:
    df_excel = pd.read_excel(last_excel)
    NEW_EXCEL_NAME = f"{OUTPUT_DIR}/{next_version(last_excel)}"
else:
    df_excel = pd.DataFrame(columns=df_csv.columns)
    NEW_EXCEL_NAME = f"{OUTPUT_DIR}/{OUTPUT_PREFIX}1.0{OUTPUT_SUFFIX}"

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
    df_updated = df_updated[
        ~df_updated.set_index(KEY_COLUMNS).index.isin(to_remove.set_index(KEY_COLUMNS).index)
        ]

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
if ( 'action' in df_updated.columns and
     'source' in df_updated.columns and
     'destination' in df_updated.columns ):
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
# Export Excel mis à jour
# ------------------------------
df_updated.to_excel(NEW_EXCEL_NAME, index=False)
print(f"Matrice mise à jour et enregistrée dans : {NEW_EXCEL_NAME}")
