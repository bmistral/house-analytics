# French Real Estate Insights

Un tableau de bord interactif (Dashboard) développé avec **Streamlit** pour analyser et visualiser les données immobilières en France.

Ce projet permet d'explorer les corrélations entre les prix des biens immobiliers, leurs surfaces habitables et les surfaces des terrains, tout en offrant des filtres géographiques avancés.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-Graphs-3f4f75)

## ✨ Fonctionnalités

*   ** Exploration des Données :** Visualisez les transactions immobilières à travers la France (prix, surfaces).
*   ** Filtrage Géographique Avancé :** 
    *   Filtrez par Département et par Ville.
    *   **Recherche par Rayon :** Sélectionnez une ville cible et visualisez toutes les transactions dans un rayon défini (en kilomètres) grâce au calcul de distance de Haversine.
*   ** Filtrage par Type de Bien :** Maisons, Appartements, Terrains, etc.
*   ** Visualisations Interactives :**
    *   **Carte Géolocalisée** (`plotly.express.scatter_mapbox`) : Visualisez la répartition spatiale et les prix des biens sur une carte.
    *   **Matrice de Corrélation** : Observez les liens statistiques entre le prix, la surface habitable et la surface du terrain.
    *   **Nuages de Points (Scatter Plots)** : Analysez la relation directe entre le prix et les différentes surfaces.
*   ** Tableau de Données Brutes :** Consultez, triez et filtrez les données tabulaires directement dans l'interface, similaire à Excel.

## 📊 Source des Données (DVF)

Les données utilisées par cette application proviennent de la base de données ouverte **Demandes de Valeurs Foncières (DVF)**, publiée par la Direction Générale des Finances Publiques (DGFiP). 

Pour l'année 2025, vous pouvez télécharger les données géolocalisées au format CSV directement depuis data.gouv.fr :
👉 [https://files.data.gouv.fr/geo-dvf/latest/csv](https://files.data.gouv.fr/geo-dvf/latest/csv)

## 🛠️ Prérequis

Assurez-vous d'avoir installé **Conda** ou **Python** (version 3.10 ou supérieure) sur votre machine.

Un script de téléchargement automatique est inclus pour récupérer les données de 2023 à 2025. Sous Linux/Mac, exécutez simplement la commande `bash fetch_data.sh` à la racine du projet. 

Les données seront automatiquement placées dans le dossier `./data/` au format `[année]_full.csv` (exemple : `data/2025_full.csv`). Ces fichiers doivent au moins contenir les colonnes `valeur_fonciere`, `code_departement`, `nom_commune`, `type_local`, `surface_reelle_bati`, `surface_terrain`, `latitude`, `longitude`.

## 🚀 Installation & Lancement

Vous pouvez choisir d'installer ce projet avec `conda` ou avec `pip`.

### Option 1 : Utilisation de Conda (Recommandé)

Un fichier `environment.yml` est fourni pour répliquer l'environnement exact.

1. **Créer l'environnement :**
   ```bash
   conda env create -f environment.yml
   ```
2. **Activer l'environnement :**
   ```bash
   conda activate house
   ```
3. **Lancer le dashboard Streamlit :**
   ```bash
   streamlit run app.py
   ```

### Option 2 : Utilisation de Pip et Virtualenv

Si vous préférez ne pas utiliser Conda, vous pouvez utiliser un environnement virtuel standard Python.

1. **Créer et activer un environnement virtuel (optionnel mais recommandé) :**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # ou
   .\venv\Scripts\activate   # Sur Windows
   ```
2. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```
3. **Lancer le dashboard Streamlit :**
   ```bash
   streamlit run app.py
   ```

## 📂 Structure du Projet

```text
house/
│
├── app.py                # Point d'entrée principal (cœur de l'application Streamlit)
├── fetch_data.sh         # Script Bash automatisé pour télécharger les données DVF (2023-2025)
├── requirements.txt      # Liste des dépendances pour pip
├── environment.yml       # Définition de l'environnement pour conda
├── README.md             # Ce fichier de documentation
│
└── data/                 # Dossier contenant la base de données (généré par fetch_data.sh)
    ├── 2025_full.csv     # Données 2025
    ├── 2024_full.csv     # Données 2024
    └── 2023_full.csv     # Données 2023
```

## 🤝 Contribution
Ce projet a été construit dans un but d'analyse de données de bout-en-bout. Toute suggestion d'amélioration de la performance (ex: passage à `duckdb` ou `polars` pour des jeux de données de plusieurs Go) est la bienvenue.
