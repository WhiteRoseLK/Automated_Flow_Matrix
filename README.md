![Pylint](https://img.shields.io/endpoint?url=https://whiterose.fr/Automated_Flow_Matrix/pylint.json)

# FlowMatrix - Gestionnaire de Flux Réseau

Suite d'outils Python pour la gestion, l'analyse et l'automatisation des flux réseau dans un environnement d'entreprise. Ce projet facilite la création de matrices de flux, l'enrichissement avec des données CMDB, et l'export vers des formats utilisables par les outils d'automatisation.

## 🎆 Vue d'ensemble

FlowMatrix est conçu pour automatiser la gestion des flux réseau à travers plusieurs étapes :

1. **Peuplement des données** - Enrichissement des flux avec les informations CMDB
2. **Calcul de routage** - Détermination des next hop basés sur les tables de routage firewall
3. **Export multi-format** - Génération de fichiers YAML Ansible et matrices Excel
4. **Gestion des versions** - Versioning automatique des matrices de flux

## 📋 Composants principaux

### 🔄 data_population.py
**Enrichissement des flux avec la CMDB**

- Lit `flows.csv` (flux de base) et `cmdb_network.csv` (correspondances réseau/zone)
- Ajoute les zones sources/destinations basées sur les adresses IP
- Applique les préfixes de type (P_ pour Production, A_ pour Admin, etc.)
- Génère `flows_populated.csv` enrichi

```bash
python3 data_population.py
```

### 📤 flux_exporter.py  
**Export vers fichiers YAML Ansible**

- Lit `flows_populated.csv`
- Groupe les flux par machine source
- Génère un fichier YAML par source dans `YAML_Output/`
- Format compatible Ansible pour automatisation

```bash
python3 flux_exporter.py
```

### 📈 update_matrix.py
**Gestionnaire de matrice Excel avec versioning**

- Met à jour les matrices Excel existantes
- Versioning automatique (Matrix_v1.0.xlsx → Matrix_v1.1.xlsx)
- Enrichissement avec zones réseau
- Gestion des actions (ajout/suppression/modification)

```bash
python3 update_matrix.py
```

### 🔀 Modules/Stormshield/next_hop_calculator.py
**Calculateur de Next Hop**

- Utilise la table de routage extraite du firewall Stormshield
- Calcule le next hop pour chaque flux (DIRECT ou IP gateway)
- Met à jour directement `flows_populated.csv`

```bash
cd Modules/Stormshield
python3 next_hop_calculator.py
```

## 🗂️ Structure des fichiers

```
FlowMatrix/
├── Input/
│   ├── flows.csv              # Flux réseau de base
│   ├── flows_populated.csv    # Flux enrichis (généré)
│   └── cmdb_network.csv       # Correspondances IP/Zone/Type
├── YAML_Output/               # Fichiers YAML par source (généré)
├── Flow_Matrix/               # Matrices Excel versionnées (généré)
├── Modules/
│   └── Stormshield/
│       ├── routing_table_FW-1.json     # Table de routage (Ansible)
│       └── next_hop_calculator.py      # Calculateur next hop
├── data_population.py          # Script d'enrichissement CMDB
├── flux_exporter.py            # Export YAML Ansible  
├── update_matrix.py            # Gestionnaire matrice Excel
└── README.md                  # Cette documentation
```

## 🚀 Workflow complet

### 1. Préparation des données
```bash
# 1. Placer flows.csv dans Input/
# 2. S'assurer que cmdb_network.csv existe dans Input/
```

### 2. Enrichissement avec la CMDB
```bash
python3 data_population.py
# → Génère flows_populated.csv avec zones et préfixes
```

### 3. Calcul des next hop (optionnel)
```bash
cd Modules/Stormshield
# 1. Exécuter le playbook Ansible pour obtenir routing_table_FW-1.json
ansible-playbook -i inventory.yml gateway.yml
# 2. Calculer les next hop
python3 next_hop_calculator.py
# → Met à jour flows_populated.csv avec la colonne next_hop
```

### 4. Export multi-format
```bash
# Export YAML pour Ansible
python3 flux_exporter.py
# → Génère des fichiers .yml dans YAML_Output/

# Mise à jour matrice Excel
python3 update_matrix.py  
# → Crée/met à jour Matrix_vX.Y.xlsx dans Flow_Matrix/
```

## 📈 Format des données

### flows.csv (entrée)
```csv
source_name,source_ip,destination_name,destination_ip,port,protocol,description
EC-CLIENT-A,192.168.10.1,EP-CLIENT-A,10.10.20.1,22,tcp,"Log collection from clients"
```

### flows_populated.csv (généré)
```csv
source_name,source_ip,source_zone,destination_name,destination_ip,destination_zone,port,protocol,description,next_hop
P_EC-CLIENT-A,192.168.10.1,Enclave_client-A,P_EP-CLIENT-A,10.10.20.1,Collecte,22,tcp,"Log collection",10.0.0.1
```

### cmdb_network.csv (configuration)
```csv
sous-reseau,zone,type
192.168.10.0/24,Enclave_client-A,Production
10.10.20.0/24,Collecte,Production
172.16.0.0/24,Admin,Admin
```

## 🔧 Prérequis

### Python
- Python 3.6+
- pandas
- ipaddress (inclus)
- pyyaml
- openpyxl (pour Excel)

```bash
pip install pandas pyyaml openpyxl
```

### Ansible (pour next hop)
- ansible-core
- stormshield.sns collection

```bash
pip install ansible-core
ansible-galaxy collection install stormshield.sns
```

## 📈 Exemples d'utilisation

### Scénario 1: Nouveau déploiement
```bash
# 1. Créer flows.csv avec les nouveaux flux
# 2. Enrichir avec CMDB
python3 data_population.py
# 3. Exporter pour Ansible
python3 flux_exporter.py
```

### Scénario 2: Mise à jour de matrice existante
```bash
# 1. Modifier flows.csv (ajouter colonne 'action' si nécessaire)
# 2. Mettre à jour la matrice
python3 update_matrix.py
# → Nouvelle version créée automatiquement
```

### Scénario 3: Analyse de routage
```bash
# 1. Extraire les routes du firewall
cd Modules/Stormshield
ansible-playbook -i inventory.yml gateway.yml
# 2. Calculer les next hop
python3 next_hop_calculator.py
# 3. Analyser les résultats dans flows_populated.csv
```

## 😨 Dépannage

### Erreur "FileNotFoundError"
- Vérifier l'existence des fichiers d'entrée
- S'assurer que les répertoires existent
- Exécuter les scripts dans l'ordre correct

### Erreur de format CSV
- Vérifier l'encodage UTF-8
- S'assurer que les en-têtes correspondent au format attendu
- Pas de lignes vides en fin de fichier

### Problèmes de next hop
- Vérifier la connectivité au firewall Stormshield
- S'assurer que le fichier routing_table_FW-1.json est valide
- Contrôler les adresses IP dans flows.csv
