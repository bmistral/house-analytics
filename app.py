import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import os

# Configure the Streamlit page
st.set_page_config(
    page_title="Données Immobilières - France",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply some custom CSS for a premium look
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    /* Rendre les menus déroulants opaques */
    ul[role="listbox"] {
        background-color: white !important;
    }
    div[data-baseweb="select"] > div {
        background-color: white !important;
    }
    div[data-baseweb="popover"] > div {
        background-color: white !important;
    }
    .st-emotion-cache-16idsys p {
        font-size: 1.1rem;
        color: #475569;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loading & Processing
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_clean_data(year, nrows=None):
    """
    Loads the real estate dataset and performs initial cleaning.
    Uses st.cache_data to keep the dataframe in memory across reruns.
    """
    data_path = f"./data/{year}_full.csv"
    if not os.path.exists(data_path):
        st.error(f"Fichier de données introuvable pour l'année {year}. Exécutez le script 'fetch_data.sh' ou vérifiez le dossier './data/'.")
        st.stop()
        
    cols_to_use = [
        'valeur_fonciere', 
        'code_departement', 
        'nom_commune', 
        'type_local', 
        'surface_reelle_bati', 
        'surface_terrain',
        'latitude',
        'longitude',
        'nature_mutation',
        'nombre_pieces_principales',
        'date_mutation'
    ]
    
    # Read the CSV file
    df = pd.read_csv(
        data_path, 
        usecols=cols_to_use, 
        nrows=nrows,
        dtype={'code_departement': str}
    )
    
    # Data Cleaning
    # Drop rows where 'valeur_fonciere' (Price) is NaN
    df = df.dropna(subset=['valeur_fonciere'])
    
    # Convert numerical columns
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce')
    df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Fill missing surfaces with 0, or drop depending on the analysis needs.
    df['surface_reelle_bati'] = df['surface_reelle_bati'].fillna(0)
    df['surface_terrain'] = df['surface_terrain'].fillna(0)
    
    # Drop invalid/negative prices
    df = df[df['valeur_fonciere'] > 0]
    
    # Standardize 'type_local'
    df['type_local'] = df['type_local'].fillna('Terrain/Autre')
    
    # --- EXPERT ANALYSIS METRICS ---
    # Filter for 'Vente' only by default to avoid polluting with exchanges/donations
    # Note: case might vary, so we normalize
    df = df[df['nature_mutation'].fillna('').str.upper() == 'VENTE']
    
    # Calculate Price per m² (only for properties with living area > 0)
    df['prix_m2'] = np.where(df['surface_reelle_bati'] > 0, df['valeur_fonciere'] / df['surface_reelle_bati'], np.nan)
    
    # Clean room count
    df['nombre_pieces_principales'] = pd.to_numeric(df['nombre_pieces_principales'], errors='coerce').fillna(0)
    
    return df

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6371 * c
    return km

# -----------------------------------------------------------------------------
# Sidebar & Filtering
# -----------------------------------------------------------------------------
st.sidebar.title("🔍 Filtres")
st.sidebar.markdown("Affinez votre recherche en sélectionnant des critères spécifiques.")

st.sidebar.subheader("📅 Année")
available_years = ["2025", "2024", "2023"]
selected_year = st.sidebar.selectbox("Choisissez l'année", available_years)

with st.spinner(f"Chargement des données de {selected_year}... Cela peut prendre un moment."):
    raw_df = load_and_clean_data(selected_year)

st.sidebar.subheader("📍 Filtre Géographique")
# Filter: Department
departments = sorted(raw_df['code_departement'].astype(str).dropna().unique().tolist())
departments = [str(d) for d in departments if str(d).strip() != '']
selected_departments = st.sidebar.multiselect(
    "1. Département (Optionnel)", 
    options=departments,
    default=["31"] if "31" in departments else None,
    help="Choisissez un ou plusieurs départements pour restreindre la liste des villes."
)

filtered_by_dept = raw_df[raw_df['code_departement'].astype(str).isin(selected_departments)] if selected_departments else raw_df
cities = sorted(filtered_by_dept['nom_commune'].dropna().unique().tolist())

# Find index of Toulouse for default selection
default_city_index = 0
# Case insensitive check for Toulouse
toulouse_options = [i for i, c in enumerate(cities) if c.upper() == "TOULOUSE"]
if toulouse_options:
    default_city_index = toulouse_options[0] + 1

selected_city = st.sidebar.selectbox(
    "2. Ville de référence", 
    options=["-- Aucune --"] + cities,
    index=default_city_index,
    help="Choisissez une ville autour de laquelle chercher."
)

radius_km = st.sidebar.slider("3. Rayon de recherche (km)", min_value=1, max_value=100, value=10, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("🏠 Type de bien")

# Filter: Property Type
property_types = sorted(raw_df['type_local'].dropna().unique().tolist())
default_types = [t for t in property_types if t in ["Maison", "Appartement"]]

selected_types = st.sidebar.multiselect(
    "Type de bien", 
    options=property_types,
    default=default_types if default_types else property_types,
    help="Filtrer par type de propriété."
)

st.sidebar.markdown("---")
st.sidebar.subheader("💎 Expertise Métiers")
analysis_metric = st.sidebar.radio(
    "Métrique principale",
    ["Prix Total (€)", "Prix au m² (€/m²)"],
    index=0
)
metric_col = 'valeur_fonciere' if analysis_metric == "Prix Total (€)" else 'prix_m2'
metric_label = "Prix (€)" if analysis_metric == "Prix Total (€)" else "Prix au m² (€/m²)"

# -----------------------------------------------------------------------------
# Apply Filters
# -----------------------------------------------------------------------------
filtered_df = raw_df.copy()

if selected_types:
    filtered_df = filtered_df[filtered_df['type_local'].isin(selected_types)]

city_center = None
if selected_city and selected_city != "-- Aucune --":
    # Get the reference city's coordinates (mean of its data points)
    city_data = raw_df[raw_df['nom_commune'] == selected_city]
    if not city_data.empty:
        center_lat = city_data['latitude'].mean()
        center_lon = city_data['longitude'].mean()
        if pd.notna(center_lat) and pd.notna(center_lon):
            city_center = (center_lat, center_lon)
            # Calculate distance for all rows that have valid coordinates
            valid_coords = filtered_df.dropna(subset=['latitude', 'longitude']).copy()
            distances = haversine(center_lat, center_lon, valid_coords['latitude'], valid_coords['longitude'])
            # Filter by radius
            filtered_df = valid_coords[distances <= radius_km]
        else:
            st.sidebar.warning("La ville sélectionnée n'a pas de coordonnées GPS valides.")
    else:
        st.sidebar.warning("Aucune donnée pour cette ville.")
elif selected_departments:
    # If no city is selected but departments are, filter by department
    filtered_df = filtered_df[filtered_df['code_departement'].astype(str).isin(selected_departments)]

# -----------------------------------------------------------------------------
# Main Dashboard Layout
# -----------------------------------------------------------------------------
st.title("🇫🇷 Analyse des Données Immobilières en France")
st.markdown("Explorez les corrélations entre les prix des biens, les surfaces habitables et les surfaces des terrains à travers la France.")

# KPI Row
st.markdown("### 📊 Indicateurs Clés")
col1, col2, col3, col4 = st.columns(4)

total_transactions = len(filtered_df)
avg_price = filtered_df['valeur_fonciere'].mean() if total_transactions > 0 else 0
avg_living_area = filtered_df[filtered_df['surface_reelle_bati'] > 0]['surface_reelle_bati'].mean()
avg_land_area = filtered_df[filtered_df['surface_terrain'] > 0]['surface_terrain'].mean()

col1.metric("Total des Transactions", f"{total_transactions:,}")
col2.metric("Prix Moyen", f"{avg_price:,.0f} €" if not np.isnan(avg_price) else "N/A")

if analysis_metric == "Prix au m² (€/m²)":
    avg_m2 = filtered_df['prix_m2'].mean()
    col3.metric("Prix m² Moyen", f"{avg_m2:,.0f} €/m²" if not np.isnan(avg_m2) else "N/A")
else:
    col3.metric("Surface Habitable Moyenne", f"{avg_living_area:,.0f} m²" if not np.isnan(avg_living_area) else "N/A")

col4.metric("Surface Terrain Moyenne", f"{avg_land_area:,.0f} m²" if not np.isnan(avg_land_area) else "N/A")

st.markdown("---")

if total_transactions == 0:
    st.warning("Aucune donnée disponible pour ces filtres. Veuillez ajuster vos critères.")
    st.stop()
elif total_transactions > 100000:
    st.info(f"Échantillonnage des données. Pour des raisons de performances de la carte et des nuages de points, un échantillon aléatoire de 100 000 points est utilisé (sur les {total_transactions:,} disponibles).")
    plot_df = filtered_df.sample(100000, random_state=42)
else:
    plot_df = filtered_df

# -----------------------------------------------------------------------------
# Map Visualization
# -----------------------------------------------------------------------------
st.markdown("### 🗺️ Carte des Transactions")
map_df = plot_df.dropna(subset=['latitude', 'longitude'])

if not map_df.empty:
    if len(map_df) > 10000:
        st.caption("Pour des raisons de performance, seules 10 000 transactions sont affichées sur la carte.")
        map_draw_df = map_df.sample(10000, random_state=42)
    else:
        map_draw_df = map_df

    # Configure map
    center_coord = {"lat": city_center[0], "lon": city_center[1]} if city_center else {"lat": 46.22, "lon": 2.21} # Par défaut centre de la France
    zoom_level = 11 if city_center else 5

    # Create a circle GeoJSON for visualization if a city is selected
    layers = []
    if city_center:
        # Generate points for a circle
        angles = np.linspace(0, 2*np.pi, 100)
        # Earth radius in km
        R = 6371.0
        d_lat = radius_km / R
        d_lon = radius_km / (R * np.cos(np.pi * city_center[0] / 180.0))
        
        circle_lat = city_center[0] + np.degrees(d_lat * np.cos(angles))
        circle_lon = city_center[1] + np.degrees(d_lon * np.sin(angles))
        
        layers = [{
            "source": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[list(z) for z in zip(circle_lon, circle_lat)]]
                    }
                }]
            },
            "type": "fill",
            "color": "rgba(255, 0, 0, 0.15)", # Very light red fill
            "below": "traces"
        }, {
            "source": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [list(z) for z in zip(circle_lon, circle_lat)]
                    }
                }]
            },
            "type": "line",
            "color": "red",
            "line": {"width": 2}
        }]

    # Calculate price percentile for better color distribution on the map
    # We use the 95th percentile as the max for the color scale to avoid outliers squashing the range
    max_val_map = map_draw_df[metric_col].quantile(0.95) if not map_draw_df.empty else 10000
    if max_val_map == 0 or np.isnan(max_val_map): max_val_map = 10000

    fig_map = px.scatter_mapbox(
        map_draw_df, 
        lat="latitude", 
        lon="longitude", 
        color=metric_col,
        hover_name="nom_commune",
        opacity=0.35, # Points more transparent as requested
        hover_data={
            "latitude": False,
            "longitude": False,
            "valeur_fonciere": ":.0f", 
            "prix_m2": ":.0f",
            "surface_reelle_bati": True, 
            "surface_terrain": True,
            "type_local": True,
            "nombre_pieces_principales": True
        },
        color_continuous_scale="Plasma", # More vibrant scale
        range_color=[0, max_val_map], # Clip color scale to handle outliers
        zoom=zoom_level,
        center=center_coord,
        height=600,
        labels={metric_col: metric_label}
    )
    
    # Use open-street-map for a "less transparent" / more vivid background
    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_layers=layers,
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    st.plotly_chart(fig_map, width="stretch", config={'scrollZoom': True})
else:
    st.info("Aucune donnée géolocalisée à afficher.")

st.markdown("---")

# -----------------------------------------------------------------------------
# Outlier Filtering for Better Visualization
# -----------------------------------------------------------------------------
# We often need to filter upper percentiles to make scatter plots legible
price_limit = plot_df['valeur_fonciere'].quantile(0.95)
living_area_limit = plot_df['surface_reelle_bati'].quantile(0.98)
land_area_limit = plot_df['surface_terrain'].quantile(0.95)

vis_df = plot_df[
    (plot_df['valeur_fonciere'] <= price_limit) &
    (plot_df['surface_reelle_bati'] <= living_area_limit) &
    (plot_df['surface_terrain'] <= land_area_limit)
]

# -----------------------------------------------------------------------------
# Visualizations: Correlations
# -----------------------------------------------------------------------------
st.markdown("### 📈 Analyse de Corrélation")

# Calculate Correlation Matrix
# We only want to correlate numerical columns where values are non-zero for meaningful results
corr_df = filtered_df[['valeur_fonciere', 'surface_reelle_bati', 'surface_terrain']].copy()
# Replace 0s with NaN for correlation calculation to avoid skewing (e.g., apartments have 0 land)
corr_df['surface_reelle_bati'] = corr_df['surface_reelle_bati'].replace(0, np.nan)
corr_df['surface_terrain'] = corr_df['surface_terrain'].replace(0, np.nan)
corr_matrix = corr_df.corr(method='pearson')

# Layout for plots
col_plot1, col_plot2 = st.columns([2, 1])

with col_plot2:
    st.markdown("#### Matrice de Corrélation")
    
    # Create an interactive heatmap using Plotly Graph Objects
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=['Prix', 'Surface Habitable', 'Surface Terrain'],
        y=['Prix', 'Surface Habitable', 'Surface Terrain'],
        colorscale='Viridis',
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        hoverinfo="text"
    ))
    fig_corr.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_corr, width="stretch")

with col_plot1:
    st.markdown("#### Prix vs Surface Habitable")
    # We filter out 0 living area for this specific plot
    viz_living = vis_df[vis_df['surface_reelle_bati'] > 0]
    
    if len(viz_living) > 0:
        fig_scatter1 = px.scatter(
            viz_living, 
            x='surface_reelle_bati', 
            y='valeur_fonciere',
            color='type_local',
            opacity=0.5,
            labels={
                'surface_reelle_bati': 'Surface Habitable (m²)', 
                'valeur_fonciere': 'Prix (€)',
                'type_local': 'Type de Bien'
            },
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_scatter1.update_layout(
            margin=dict(t=10, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_scatter1, width="stretch")
    else:
        st.info("Pas assez de données avec une surface habitable > 0 après filtrage.")

st.markdown("---")

# Price vs Land Area Scatter Plot
st.markdown("#### Prix vs Surface Terrain")
viz_land = vis_df[vis_df['surface_terrain'] > 0]

if len(viz_land) > 0:
    fig_scatter2 = px.scatter(
        viz_land, 
        x='surface_terrain', 
        y='valeur_fonciere',
        color='type_local',
        opacity=0.5,
        labels={
            'surface_terrain': 'Surface Terrain (m²)', 
            'valeur_fonciere': 'Prix (€)',
            'type_local': 'Type de Bien'
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_scatter2.update_layout(
         margin=dict(t=10, l=10, r=10, b=10),
         paper_bgcolor='rgba(0,0,0,0)',
         plot_bgcolor='rgba(0,0,0,0)',
         height=500
    )
    st.plotly_chart(fig_scatter2, width="stretch")
else:
    st.info("Pas assez de données avec une surface de terrain > 0 après filtrage.")

# -----------------------------------------------------------------------------
# Expert Segment Analysis: Room Count
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🏘️ Analyse par Typologie (Nombre de pièces)")
col_seg1, col_seg2 = st.columns([1, 2])

# Filter out 0 pieces for meaningful typology analysis
seg_df = filtered_df[filtered_df['nombre_pieces_principales'] > 0].copy()
# Simplify pieces: 1, 2, 3, 4, 5+
seg_df['typologie'] = seg_df['nombre_pieces_principales'].apply(lambda x: f"{int(x)} P" if x < 5 else "5+ P")
seg_order = ["1 P", "2 P", "3 P", "4 P", "5+ P"]

with col_seg1:
    st.markdown("#### Répartition des Ventes")
    type_counts = seg_df['typologie'].value_counts().reindex(seg_order).fillna(0)
    fig_pie = px.pie(
        names=type_counts.index, 
        values=type_counts.values,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig_pie, width="stretch")

with col_seg2:
    st.markdown("#### Prix au m² Moyen par Typologie")
    avg_prix_m2 = seg_df.groupby('typologie')['prix_m2'].mean().reindex(seg_order)
    fig_bar = px.bar(
        x=avg_prix_m2.index, 
        y=avg_prix_m2.values,
        labels={'x': 'Typologie', 'y': 'Prix au m² (€/m²)'},
        color=avg_prix_m2.index,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    # Add labels on bars
    fig_bar.update_traces(texttemplate='%{y:,.0f} €', textposition='outside')
    fig_bar.update_layout(height=350, showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig_bar, width="stretch")

# -----------------------------------------------------------------------------
# Raw Data Exploration
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 📋 Exploration des Données Brutes")
st.markdown("Visualisez et filtrez les données sélectionnées. Cliquez sur les en-têtes de colonnes pour les trier.")

# Control display size
col_table1, col_table2 = st.columns([1, 2])

with col_table1:
    display_mode = st.radio(
        "Mode d'affichage du tableau",
        ["Top N", "Toutes les données"],
        index=0,
        help="L'affichage de toutes les données peut être lent."
    )

with col_table2:
    if display_mode == "Top N":
        n_rows = st.slider("Nombre de lignes à afficher", min_value=100, max_value=10000, value=2000, step=100)
        display_df = filtered_df.head(n_rows)
        st.info(f"Affichage des {len(display_df):,} premières lignes sur {len(filtered_df):,} disponibles.")
    else:
        display_df = filtered_df
        st.warning(f"⚠️ Affichage de la totalité des {len(filtered_df):,} lignes. Cela peut impacter les performances de votre navigateur.")

# formatting the float columns to look better in the table
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "valeur_fonciere": st.column_config.NumberColumn(
            "Prix (€)",
            help="Prix du Bien",
            format="%d €",
        ),
        "surface_reelle_bati": st.column_config.NumberColumn(
            "Surface Habitable (m²)",
            format="%d m²",
        ),
        "surface_terrain": st.column_config.NumberColumn(
            "Surface Terrain (m²)",
            format="%d m²",
        ),
        "code_departement": "Code Dépt",
        "nom_commune": "Ville",
        "type_local": "Type de Bien"
    }
)
