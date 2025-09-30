import os
import pandas as pd
import ipaddress

INPUT_DIR = "Input"
SUBNET_FILE = "cmdb_network.csv"
SUBNET_PATH = f"{INPUT_DIR}/{SUBNET_FILE}"
CSV_FILE = 'flows.csv'
CSV_PATH = f"{INPUT_DIR}/{CSV_FILE}"

def insert_column_after(df, new_col_name, new_col_values, after_col):
    idx = df.columns.get_loc(after_col) + 1
    df.insert(idx, new_col_name, new_col_values)
    return df

def ip_to_zone(ip, subnet_df):
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
    zone_source = ip_to_zone(row['source_ip'], df_subnets)
    zone_destination = ip_to_zone(row['destination_ip'], df_subnets)
    row['source_name'] = f"{zone_source['type'][0]}_{row['source_name']}"
    row['source_zone'] = zone_source['zone']
    row['destination_name'] = f"{zone_destination['type'][0]}_{row['destination_name']}"
    row['destination_zone'] = zone_destination['zone']
    return row

# ------------------------------
# Lecture CSV et table de correspondance
# ------------------------------
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"Le fichier CSV {CSV_PATH} n'existe pas.")
if not os.path.exists(SUBNET_PATH):
    raise FileNotFoundError(f"Le fichier de correspondance {SUBNET_PATH} n'existe pas.")

df_csv = pd.read_csv(CSV_PATH)
df_subnets = pd.read_csv(SUBNET_PATH)

# ------------------------------
# Complétion des flux avec les infos de la CMDB
# ------------------------------

df_csv = insert_column_after(df_csv, 'source_zone', None, 'source_ip')
df_csv = insert_column_after(df_csv, 'destination_zone', None, 'destination_ip')

df_population = df_csv.apply(dataPopulation, axis=1)

df_population.to_csv(f"{INPUT_DIR}/flows_populated.csv", index=False)