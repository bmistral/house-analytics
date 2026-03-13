import streamlit as st
import pandas as pd
import numpy as np
import os
import utils
import visuals

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
    .main { background-color: #f8fafc; }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    h1, h2, h3 { color: #1e293b; font-family: 'Inter', sans-serif; }
    ul[role="listbox"], div[data-baseweb="select"] > div, div[data-baseweb="popover"] > div { background-color: white !important; }
    .st-emotion-cache-16idsys p { font-size: 1.1rem; color: #475569; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar & Filtering
# -----------------------------------------------------------------------------
st.sidebar.title("🔍 Filtres")
st.sidebar.markdown("Affinez votre recherche en sélectionnant des critères spécifiques.")

st.sidebar.subheader("📅 Année")
available_years = ["2025", "2024", "2023"]
selected_year = st.sidebar.selectbox("Choisissez l'année", available_years)

with st.spinner(f"Chargement des données de {selected_year}..."):
    raw_df = utils.load_and_clean_data(selected_year)
    if raw_df is None:
        st.error(f"Données introuvables pour {selected_year}.")
        st.stop()

st.sidebar.subheader("📍 Filtre Géographique")
departments = sorted(raw_df['code_departement'].astype(str).dropna().unique().tolist())
selected_departments = st.sidebar.multiselect(
    "1. Département (Optionnel)", options=[d for d in departments if d.strip()],
    default=["31"] if "31" in departments else None
)

filtered_by_dept = raw_df[raw_df['code_departement'].astype(str).isin(selected_departments)] if selected_departments else raw_df
cities = sorted(filtered_by_dept['nom_commune'].dropna().unique().tolist())

default_city_index = ([i for i, c in enumerate(cities) if c.upper() == "TOULOUSE"] or [-1])[0] + 1

selected_city = st.sidebar.selectbox("2. Ville de référence", options=["-- Aucune --"] + cities, index=default_city_index)
radius_km = st.sidebar.slider("3. Rayon de recherche (km)", min_value=1, max_value=100, value=10)

st.sidebar.markdown("---")
st.sidebar.subheader("🏠 Type de bien")
property_types = sorted(raw_df['type_local'].dropna().unique().tolist())
selected_types = st.sidebar.multiselect(
    "Type de bien", options=property_types,
    default=[t for t in property_types if t in ["Maison", "Appartement"]] or property_types
)

st.sidebar.markdown("---")
st.sidebar.subheader("💎 Expertise Métiers")
analysis_metric = st.sidebar.radio("Métrique principale", ["Prix Total (€)", "Prix au m² (€/m²)"])
metric_col = 'valeur_fonciere' if analysis_metric == "Prix Total (€)" else 'prix_m2'
metric_label = "Prix (€)" if analysis_metric == "Prix Total (€)" else "Prix au m² (€/m²)"

# -----------------------------------------------------------------------------
# Apply Filters
# -----------------------------------------------------------------------------
filtered_df = raw_df.copy()

# By default, we focus on sales for the main dashboard (Overview, Expert, Estimate)
# But we'll allow full exploration in the Raw Data tab
global_filtered_df = filtered_df[filtered_df['nature_mutation'].fillna('').str.upper() == 'VENTE']

if selected_types:
    global_filtered_df = global_filtered_df[global_filtered_df['type_local'].isin(selected_types)]

city_center = None
if selected_city != "-- Aucune --":
    city_center = utils.get_city_center(raw_df, selected_city)
    if city_center:
        global_filtered_df = utils.filter_data_by_radius(global_filtered_df, city_center, radius_km)
    else:
        st.sidebar.warning("Coordonnées GPS introuvables pour cette ville.")
elif selected_departments:
    global_filtered_df = global_filtered_df[global_filtered_df['code_departement'].astype(str).isin(selected_departments)]

# Alias for compatibility with existing code in tabs
filtered_df = global_filtered_df

# -----------------------------------------------------------------------------
# Main Dashboard Layout
# -----------------------------------------------------------------------------
st.title("Analyse des Données Immobilières en France")
st.markdown("Explorez les tendances immobilières à travers la France.")

tab_overview, tab_expert, tab_estimer, tab_data = st.tabs(["🏠 Vue d'ensemble", "💎 Analyse Expert", "📍 Estimer & Comparer", "📋 Données Brutes"])

with tab_overview:
    st.markdown("### 📊 Indicateurs Clés")
    total_tx = len(filtered_df)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions", f"{total_tx:,}")
    col2.metric("Prix Moyen", f"{filtered_df['valeur_fonciere'].mean():,.0f} €" if total_tx > 0 else "N/A")
    
    if analysis_metric == "Prix au m² (€/m²)":
        col3.metric("Prix m² Moyen", f"{filtered_df['prix_m2'].mean():,.0f} €/m²" if total_tx > 0 else "N/A")
    else:
        col3.metric("Surf. Hab. Moyenne", f"{filtered_df[filtered_df['surface_reelle_bati'] > 0]['surface_reelle_bati'].mean():,.0f} m²" if total_tx > 0 else "N/A")
    col4.metric("Surf. Terr. Moyenne", f"{filtered_df[filtered_df['surface_terrain'] > 0]['surface_terrain'].mean():,.0f} m²" if total_tx > 0 else "N/A")

    if total_tx == 0:
        st.warning("Aucune donnée pour ces filtres.")
        st.stop()
    
    plot_df = filtered_df.sample(min(total_tx, 100000), random_state=42) if total_tx > 100000 else filtered_df

    st.markdown("---")
    st.markdown("### 🗺️ Carte des Transactions")
    map_draw_df = plot_df.dropna(subset=['latitude', 'longitude'])
    if not map_draw_df.empty:
        st.plotly_chart(visuals.create_map_fig(map_draw_df.sample(min(len(map_draw_df), 10000), random_state=42), metric_col, metric_label, city_center, radius_km, 11 if city_center else 5), config={'scrollZoom': True})
    
    st.markdown("---")
    st.markdown("### 📈 Analyse de Corrélation")
    vis_df = plot_df[
        (plot_df['valeur_fonciere'] <= plot_df['valeur_fonciere'].quantile(0.95)) &
        (plot_df['surface_reelle_bati'] <= plot_df['surface_reelle_bati'].quantile(0.98)) &
        (plot_df['surface_terrain'] <= plot_df['surface_terrain'].quantile(0.95))
    ]
    
    c_plot1, c_plot2 = st.columns([2, 1])
    with c_plot2:
        corr_matrix = filtered_df[['valeur_fonciere', 'surface_reelle_bati', 'surface_terrain']].replace(0, np.nan).corr()
        st.plotly_chart(visuals.create_correlation_heatmap(corr_matrix))
    with c_plot1:
        viz_living = vis_df[vis_df['surface_reelle_bati'] > 0]
        if not viz_living.empty:
            st.plotly_chart(visuals.create_scatter_plot(viz_living, 'surface_reelle_bati', 'valeur_fonciere', 'type_local', 'Surf. Habitable (m²)', 'Prix (€)'))

    st.markdown("#### Prix vs Surface Terrain")
    viz_land = vis_df[vis_df['surface_terrain'] > 0]
    if not viz_land.empty:
        st.plotly_chart(visuals.create_scatter_plot(viz_land, 'surface_terrain', 'valeur_fonciere', 'type_local', 'Surf. Terrain (m²)', 'Prix (€)'))

with tab_expert:
    st.markdown("### 🏘️ Analyse par Typologie")
    seg_df = filtered_df[filtered_df['nombre_pieces_principales'] > 0].copy()
    if not seg_df.empty:
        seg_df['typologie'] = seg_df['nombre_pieces_principales'].apply(lambda x: f"{int(x)} P" if x < 5 else "5+ P")
        seg_order = ["1 P", "2 P", "3 P", "4 P", "5+ P"]
        
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            counts = seg_df['typologie'].value_counts().reindex(seg_order).fillna(0)
            st.plotly_chart(visuals.create_pie_chart(counts.index, counts.values))
        with col_s2:
            avg_m2 = seg_df.groupby('typologie')['prix_m2'].mean().reindex(seg_order)
            st.plotly_chart(visuals.create_bar_chart(avg_m2.index, avg_m2.values, 'Typologie', 'Prix au m²', avg_m2.index))
        
        st.plotly_chart(visuals.create_boxplot(seg_df, 'typologie', metric_col, 'type_local', 'Pièces', metric_label, {"typologie": seg_order}))
    else:
        st.info("Données de pièces insuffisantes.")

with tab_estimer:
    st.markdown("### 📍 Outils d'Aide à la Revente")
    col_e1, col_e2 = st.columns([1, 1])
    
    with col_e1:
        st.markdown("#### 🧮 Simulateur")
        with st.container(border=True):
            in_type = st.selectbox("Type de bien", options=selected_types or property_types)
            is_t = "Terrain" in in_type
            if not is_t:
                in_surf, in_pcs = st.number_input("Surf. Hab (m²)", 9, 1000, 100), st.number_input("Pièces", 1, 20, 4)
            else:
                in_surf, in_pcs = 0, 0
            in_terr = st.number_input("Surf. Terrain (m²)", 0, 100000, 500 if is_t else 0)
            
            st.info("**Méthodologie :** Basé sur la médiane et les percentiles (25/75) des ventes réelles filtrées.")
            
            local_df = filtered_df[filtered_df['type_local'] == in_type]
            stats = utils.get_estimation_stats(local_df, in_surf, in_terr, is_t)
            
            if stats:
                st.subheader(f"{stats['median']:,.0f} €")
                st.caption(f"Marché : **{stats['low']:,.0f} € - {stats['high']:,.0f} €**")
                st.caption(f"Prix m² médian : {stats['median_m2']:,.0f} €/m²")
            else:
                st.warning("Données locales insuffisantes.")
                
            if not is_t:
                st.markdown("---")
                st.markdown("#### 🏗️ Analyse Foncière (Terrain seul)")
                land_d = filtered_df[filtered_df['type_local'].str.contains('Terrain', case=False, na=False)].copy()
                if not land_d.empty:
                    land_d.loc[:, 'prix_m2_terrain'] = land_d['valeur_fonciere'] / land_d['surface_terrain'].replace(0, np.nan)
                    m_land_m2 = land_d['prix_m2_terrain'].median()
                    est_land = in_terr * m_land_m2
                    st.write(f"Prix médian terrain nu : **{m_land_m2:,.0f} €/m²**")
                    if in_terr > 0:
                        st.write(f"Valeur terrain seul : **{est_land:,.0f} €**")
                        if stats and est_land > stats['median']:
                            st.success("💡 Valeur terrain > Valeur bâtie. Division parcellaire suggérée.")
                else:
                    st.info("Données terrains insuffisantes.")

    with col_e2:
        st.markdown("#### 📉 Positionnement")
        if stats:
            m_suffix = "m² de terrain" if is_t else "m² habitable"
            hist_df = local_df.copy()
            hist_df.loc[:, 'prix_m2_calc'] = hist_df['valeur_fonciere'] / (hist_df['surface_terrain'] if is_t else hist_df['surface_reelle_bati']).replace(0, np.nan)
            st.plotly_chart(visuals.create_dist_histogram(hist_df, 'prix_m2_calc', f'Prix / {m_suffix}', f"Distribution ({in_type})", stats['median_m2']))

    st.markdown("---")
    st.markdown("#### 🏘️ Les 10 Voisins Similaires")
    if stats:
        bench_df = utils.calculate_similarity_score(local_df, in_surf if not is_t else in_terr, in_pcs, is_t)
        top_n = bench_df.sort_values('diff_score').head(10)
        show_cols = ['nom_commune', 'valeur_fonciere', 'surface_terrain']
        if not is_t: show_cols += ['surface_reelle_bati', 'nombre_pieces_principales']
        st.table(top_n[show_cols].rename(columns={'nom_commune': 'Ville', 'valeur_fonciere': 'Prix', 'surface_terrain': 'Terrain', 'surface_reelle_bati': 'Surface', 'nombre_pieces_principales': 'Pièces'}))

with tab_data:
    st.markdown("### 📋 Données Brutes")
    
    # Base for raw data before tab-specific filters
    # We apply same geo/dept filters as sidebar to maintain context
    raw_base_df = raw_df.copy()
    if selected_city != "-- Aucune --" and city_center:
        raw_base_df = utils.filter_data_by_radius(raw_base_df, city_center, radius_km)
    elif selected_departments:
        raw_base_df = raw_base_df[raw_base_df['code_departement'].astype(str).isin(selected_departments)]

    # Advanced Filters for Raw Data
    with st.expander("🔍 Filtres Avancés (Données Brutes uniquement)", expanded=True):
        fcol1, fcol2, fcol3 = st.columns(3)
        
        with fcol1:
            # Date Filter
            min_date = raw_base_df['date_mutation'].min()
            max_date = raw_base_df['date_mutation'].max()
            if pd.notna(min_date) and pd.notna(max_date):
                date_range = st.date_input(
                    "Période",
                    value=(min_date.date(), max_date.date()),
                    min_value=min_date.date(),
                    max_value=max_date.date()
                )
            else:
                st.info("Dates indisponibles")
                date_range = None

        with fcol2:
            # Nature Filter
            natures = sorted(raw_base_df['nature_mutation'].fillna('Inconnu').unique().tolist())
            selected_natures = st.multiselect("Nature de la mutation", options=natures, default=natures)

        with fcol3:
            # Local Type Filter (more granular than sidebar)
            types = sorted(raw_base_df['type_local'].unique().tolist())
            selected_raw_types = st.multiselect("Type de bien (Détaillé)", options=types, default=types)

    # Apply Tab-Specific Filters
    tab_df = raw_base_df.copy()
    if date_range and len(date_range) == 2:
        tab_df = tab_df[(tab_df['date_mutation'].dt.date >= date_range[0]) & (tab_df['date_mutation'].dt.date <= date_range[1])]
    if selected_natures:
        tab_df = tab_df[tab_df['nature_mutation'].fillna('Inconnu').isin(selected_natures)]
    if selected_raw_types:
        tab_df = tab_df[tab_df['type_local'].isin(selected_raw_types)]

    # Display Controls
    mode = st.radio("Affichage", ["Top N", "Toutes"], horizontal=True, key="raw_display_mode")
    if mode == "Top N":
        max_rows = len(tab_df)
        n_show = st.number_input(
            "Nombre de lignes à afficher", 
            min_value=1, 
            max_value=max(1, max_rows), 
            value=min(2000, max_rows) if max_rows > 0 else 1,
            step=100,
            key="raw_n_rows"
        )
        st.info(f"Affichage des {n_show:,} premières lignes sur {max_rows:,} disponibles après filtres.")
    else:
        n_show = len(tab_df)
        if n_show > 10000:
            st.warning(f"⚠️ Affichage de la totalité des {n_show:,} lignes. Cela peut impacter les performances de votre navigateur.")
        else:
            st.success(f"Affichage de la totalité des {n_show:,} lignes.")

    # Format Date column for display
    display_df = tab_df.head(n_show).copy()
    if 'date_mutation' in display_df.columns:
        display_df['date_mutation'] = display_df['date_mutation'].dt.strftime('%d/%m/%Y')

    st.dataframe(display_df, width='stretch', hide_index=True)

