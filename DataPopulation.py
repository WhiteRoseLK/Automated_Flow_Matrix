#!/usr/bin/env python3
"""
Script de peuplement des données de flux réseau avec les informations CMDB

Ce script :
1. Lit le fichier flows.csv contenant les flux réseau de base
2. Lit le fichier cmdb_network.csv contenant la correspondance IP/Zone/Type
3. Enrichit chaque flux avec :
   - Les zones sources et destinations basées sur les adresses IP
   - Les préfixes de type (P_, A_, etc.) basés sur le type de réseau
4. Génère flows_populated.csv avec toutes les informations enrichies

Prérequis :
- flows.csv : Fichier source avec les flux réseau
- cmdb_network.csv : Table de correspondance réseau/zone/type
"""

import os
import pandas as pd
import ipaddress

# ------------------------------
# CONFIGURATION
# ------------------------------
INPUT_DIR = "Input"
SUBNET_FILE = "cmdb_network.csv"
SUBNET_PATH = f"{INPUT_DIR}/{SUBNET_FILE}"
CSV_FILE = 'flows.csv'
CSV_PATH = f"{INPUT_DIR}/{CSV_FILE}"

# ------------------------------
# FONCTIONS UTILITAIRES
# ------------------------------

def insert_column_after(df, new_col_name, new_col_values, after_col):
    """
    Insère une nouvelle colonne dans un DataFrame après une colonne spécifiée
    
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

def ip_to_zone(ip, subnet_df):
    """
    Trouve la zone et le type correspondants à une adresse IP
    
    Args:
        ip (str): Adresse IP à analyser
        subnet_df (DataFrame): DataFrame contenant les correspondances réseau/zone/type
        
    Returns:
        dict: Ligne correspondante avec zone et type, ou None si non trouvé
    """
    try:
        ip_addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    
    for _, row in subnet_df.iterrows():
        network = ipaddress.ip_network(row['sous-reseau'])
        if ip_addr in network:
            return row
    return None

def dataPopulation(row):
    """
    Enrichit une ligne de flux avec les informations de zone et de type
    
    Args:
        row (Series): Ligne de flux à enrichir
        
    Returns:
        Series: Ligne enrichie avec zones et préfixes de type
    """
    zone_source = ip_to_zone(row['source_ip'], df_subnets)
    zone_destination = ip_to_zone(row['destination_ip'], df_subnets)
    
    # Ajouter le préfixe de type au nom (P_ pour Production, A_ pour Admin, etc.)
    row['source_name'] = f"{zone_source['type'][0]}_{row['source_name']}"
    row['source_zone'] = zone_source['zone']
    row['destination_name'] = f"{zone_destination['type'][0]}_{row['destination_name']}"
    row['destination_zone'] = zone_destination['zone']
    
    return row

# ------------------------------
# TRAITEMENT PRINCIPAL
# ------------------------------

if __name__ == "__main__":
    print("🚀 Peuplement des données de flux avec la CMDB")
    print("=" * 50)
    
    # Vérification de l'existence des fichiers
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
    
    # Ajout des colonnes de zone
    print("\n🔧 Préparation des colonnes...")
    df_csv = insert_column_after(df_csv, 'source_zone', None, 'source_ip')
    df_csv = insert_column_after(df_csv, 'destination_zone', None, 'destination_ip')

    # Génération de la colonne 'rule ID' au format R_1, R_2, ...
    rule_ids = [f"R_{i}" for i in range(1, len(df_csv) + 1)]

    # Ajout de la colonne Rule_ID
    df_csv.insert(0, 'Rule_ID', rule_ids)
    
    # Enrichissement des données
    print("🔄 Enrichissement des flux avec les informations CMDB...")
    df_population = df_csv.apply(dataPopulation, axis=1)
    
    # Sauvegarde
    output_file = f"{INPUT_DIR}/flows_populated.csv"
    df_population.to_csv(output_file, index=False)
    print(f"💾 Fichier sauvegardé : {output_file}")
    
    print("\n✅ Peuplement terminé avec succès !")
    print(f"Flux traiter : {len(df_population)}")
