#!/bin/bash

# Script pour télécharger les données DVF (Demandes de Valeurs Foncières)
# pour les années 2023, 2024 et 2025.

mkdir -p data
cd data || exit

echo "Démarrage du téléchargement des données DVF..."

for year in 2023 2024 2025; do
  if [ ! -s "${year}_full.csv" ]; then
    echo "[${year}] Téléchargement..."
    curl -L -o "${year}_full.csv.gz" "https://files.data.gouv.fr/geo-dvf/latest/csv/${year}/full.csv.gz"
    echo "[${year}] Extraction..."
    gunzip -f "${year}_full.csv.gz"
    echo "[${year}] Terminé."
  else
    echo "[${year}] Fichier ${year}_full.csv déjà présent et non vide."
  fi
done

echo "Toutes les données ont été récupérées avec succès !"
