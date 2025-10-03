#!/usr/bin/env python3
"""
Script pour calculer le next hop pour chaque flux dans flows_populated.csv
basé sur les routes du fichier routing_table_FW-1.json

Ce script :
1. Lit le fichier flows_populated.csv existant
2. Lit le fichier routing_table_FW-1.json pour obtenir les routes disponibles
3. Pour chaque flux, calcule le next hop en vérifiant :
   - Si la destination est dans le même réseau que la source (communication directe)
   - Si une route spécifique existe pour le réseau de destination
   - Sinon utilise la route par défaut
4. Ajoute la colonne next_hop au fichier CSV existant
"""

import json
import pandas as pd
import ipaddress
import sys
from pathlib import Path

def load_routing_table(routing_file):
    """
    Charge la table de routage depuis le fichier JSON
    
    Args:
        routing_file (str): Chemin vers le fichier routing_table_FW-1.json
        
    Returns:
        list: Liste des routes avec Address et Gateway
    """
    try:
        with open(routing_file, 'r') as f:
            routes = json.load(f)
        print(f"✅ Table de routage chargée: {len(routes)} routes trouvées")
        return routes
    except FileNotFoundError:
        print(f"❌ Erreur: Fichier de routage introuvable: {routing_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur: Format JSON invalide dans {routing_file}: {e}")
        return None

def load_flows(flows_file):
    """
    Charge les flux depuis le fichier CSV avec pandas
    
    Args:
        flows_file (str): Chemin vers le fichier flows_populated.csv
        
    Returns:
        pandas.DataFrame: DataFrame avec les flux
    """
    try:
        df = pd.read_csv(flows_file)
        print(f"✅ Flux chargés: {len(df)} flux trouvés")
        return df
    except FileNotFoundError:
        print(f"❌ Erreur: Fichier de flux introuvable: {flows_file}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors du chargement des flux: {e}")
        return None

def is_same_network(source_ip, dest_ip, subnet_mask=24):
    """
    Vérifie si deux adresses IP sont dans le même réseau
    
    Args:
        source_ip (str): Adresse IP source
        dest_ip (str): Adresse IP destination
        subnet_mask (int): Masque de sous-réseau (défaut /24)
        
    Returns:
        bool: True si dans le même réseau, False sinon
    """
    try:
        source_net = ipaddress.IPv4Network(f"{source_ip}/{subnet_mask}", strict=False)
        dest_addr = ipaddress.IPv4Address(dest_ip)
        return dest_addr in source_net
    except Exception:
        return False

def find_matching_route(dest_ip, routes):
    """
    Trouve la route correspondante pour une destination donnée
    
    Args:
        dest_ip (str): Adresse IP de destination
        routes (list): Liste des routes disponibles
        
    Returns:
        dict: Route correspondante ou None si aucune trouvée
    """
    try:
        dest_addr = ipaddress.IPv4Address(dest_ip)
        
        # Trier les routes par spécificité (masque le plus long d'abord)
        sorted_routes = []
        for route in routes:
            try:
                if route['Address'] == '0.0.0.0/0':
                    # Route par défaut - sera évaluée en dernier
                    sorted_routes.append((route, 0))
                else:
                    network = ipaddress.IPv4Network(route['Address'])
                    sorted_routes.append((route, network.prefixlen))
            except Exception:
                continue
        
        # Trier par longueur de préfixe (descendant)
        sorted_routes.sort(key=lambda x: x[1], reverse=True)
        
        # Chercher la première route correspondante
        for route, prefix_len in sorted_routes:
            try:
                if route['Address'] == '0.0.0.0/0':
                    # Route par défaut correspond à tout
                    return route
                else:
                    network = ipaddress.IPv4Network(route['Address'])
                    if dest_addr in network:
                        return route
            except Exception:
                continue
                
        return None
    except Exception:
        return None

def calculate_next_hop(source_ip, dest_ip, routes):
    """
    Calcule le next hop pour un flux donné
    
    Args:
        source_ip (str): Adresse IP source
        dest_ip (str): Adresse IP destination
        routes (list): Table de routage
        
    Returns:
        dict: Informations sur le next hop
    """
    result = {
        'source_ip': source_ip,
        'dest_ip': dest_ip,
        'next_hop': None
    }
    
    # Vérifier si c'est dans le même réseau (communication directe)
    if is_same_network(source_ip, dest_ip):
        result['next_hop'] = 'DIRECT'
        return result
    
    # Chercher une route correspondante
    matching_route = find_matching_route(dest_ip, routes)
    if matching_route:
        if 'Gateway' in matching_route and matching_route['Gateway']:
            result['next_hop'] = matching_route['Gateway']
        else:
            # Route sans gateway (interface directe)
            result['next_hop'] = 'DIRECT'
    else:
        result['next_hop'] = 'NO_ROUTE'
    
    return result

def main():
    """
    Fonction principale
    """
    print("🚀 Calculateur de Next Hop")
    print("=" * 50)
    
    # Chemins des fichiers
    current_dir = Path(__file__).parent
    routing_file = current_dir / "routing_table_FW-1.json"
    flows_file = current_dir.parent.parent / "Input" / "flows_populated.csv"
    
    print(f"📁 Répertoire de travail: {current_dir}")
    print(f"📋 Fichier de routage: {routing_file}")
    print(f"📊 Fichier de flux: {flows_file}")
    print()
    
    # Charger les données
    routes = load_routing_table(routing_file)
    if not routes:
        sys.exit(1)
    
    df_flows = load_flows(flows_file)
    if df_flows is None:
        sys.exit(1)
    
    print("\n📊 Analyse des routes disponibles:")
    for i, route in enumerate(routes, 1):
        gateway = route.get('Gateway', 'N/A')
        print(f"  {i}. {route['Address']} → {gateway}")
    
    print(f"\n🔄 Calcul du next hop pour {len(df_flows)} flux...")
    print("=" * 50)
    
    # Calculer le next hop pour chaque flux
    next_hops = []
    
    for i, row in df_flows.iterrows():
        source_ip = row['source_ip']
        dest_ip = row['destination_ip']
        source_name = row['source_name']
        dest_name = row['destination_name']
        
        next_hop_info = calculate_next_hop(source_ip, dest_ip, routes)
        
        next_hops.append(next_hop_info['next_hop'])
        
        # Affichage du résultat
        next_hop = next_hop_info['next_hop']
        
        print(f"  {i+1:2d}. {source_name:12s} ({source_ip:15s}) → {dest_name:12s} ({dest_ip:15s})")
        print(f"      Next Hop: {next_hop:15s}")
        
        if next_hop == 'NO_ROUTE':
            print(f"      ⚠️  ATTENTION: Pas de route trouvée pour {dest_ip}")
        elif next_hop == 'DIRECT':
            print(f"      ✅ Communication directe")
        else:
            print(f"      🔀 Via gateway {next_hop}")
        print()
    
    # Ajouter la colonne au DataFrame
    df_flows['next_hop'] = next_hops
    
    # Supprimer les colonnes route_info et route_type si elles existent
    columns_to_remove = ['route_info', 'route_type']
    for col in columns_to_remove:
        if col in df_flows.columns:
            df_flows = df_flows.drop(col, axis=1)
            print(f"🗑️ Colonne {col} supprimée")
    
    # Sauvegarder le CSV mis à jour
    try:
        df_flows.to_csv(flows_file, index=False)
        print(f"💾 Fichier CSV mis à jour: {flows_file}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    # Statistiques
    direct_count = sum(1 for nh in next_hops if nh == 'DIRECT')
    gateway_count = sum(1 for nh in next_hops if nh not in ['DIRECT', 'NO_ROUTE'])
    no_route_count = sum(1 for nh in next_hops if nh == 'NO_ROUTE')
    
    print("\n📈 Statistiques:")
    print(f"  • Communications directes: {direct_count}")
    print(f"  • Via gateway: {gateway_count}")
    print(f"  • Sans route: {no_route_count}")
    print(f"  • Total: {len(df_flows)}")
    
    print("\n✅ Colonne next_hop ajoutée au fichier flows_populated.csv")

if __name__ == "__main__":
    main()