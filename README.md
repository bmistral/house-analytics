# French Real Estate Insights

Un tableau de bord interactif (Dashboard) développé avec **Streamlit** pour analyser et visualiser les données immobilières en France.

Ce projet permet d'explorer les corrélations entre les prix des biens immobiliers, leurs surfaces habitables et les surfaces des terrains, tout en offrant des filtres géographiques avancés.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-Graphs-3f4f75)

## ✨ Fonctionnalités

Le dashboard est organisé en quatre sections majeures pour répondre aux besoins des analystes et des particuliers :

1.  **🏠 Vue d'ensemble** : 
    *   **KPIs Dynamiques** : Nombre de transactions, prix moyen, surfaces moyennes.
    *   **Carte Interactive** : Visualisation géospatiale avec échelle de couleur adaptative (clipping des outliers au 95ème percentile).
    *   **Cercle de Recherche** : Visualisation précise du rayon de recherche autour de la ville de référence.
    *   **Analyse de Corrélation** : Matrice interactive et nuages de points (Prix vs Surface).
2.  **💎 Analyse Expert** :
    *   **Métrique Prix/m²** : Basculez l'ensemble du dashboard entre le prix total et le prix au m².
    *   **Segmentation par Typologie** : Analyse détaillée par nombre de pièces (T1, T2, T3, T4, T5+).
    *   **Pureté des données** : Filtrage automatique sur les transactions de type "Vente" uniquement.
3.  **📍 Estimer & Comparer** :
    *   **Simulateur d'Estimation** : Obtenez une fourchette de prix (Bas/Médian/Haut) basée sur les données locales réelles.
    *   **Analyse Foncière** : Détermination de la valeur du terrain nu et suggestions de division parcellaire si la valeur foncière dépasse la valeur bâtie.
    *   **Benchmarking "Voisins"** : Tableau des 10 transactions les plus similaires basées sur un score de proximité (Surface, Pièces).
    *   **Positionnement Marché** : Histogramme de distribution des prix pour situer votre bien.
4.  **📋 Données Brutes** :
    *   Exploration tabulaire complète avec tri et filtrage.
    *   Mode d'affichage configurable (Top N ou Dataset complet).

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
