import pandas as pd
import numpy as np
import os
import streamlit as st

@st.cache_data(show_spinner=False)
def load_and_clean_data(year, nrows=None):
    """
    Loads the real estate dataset and performs initial cleaning.
    """
    data_path = f"./data/{year}_full.csv"
    if not os.path.exists(data_path):
        return None
        
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
    df = df.dropna(subset=['valeur_fonciere'])
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce')
    df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    df['surface_reelle_bati'] = df['surface_reelle_bati'].fillna(0)
    df['surface_terrain'] = df['surface_terrain'].fillna(0)
    
    df = df[df['valeur_fonciere'] > 0]
    
    # Standardize 'type_local'
    mask_terrain = (df['type_local'].isna()) & (df['surface_reelle_bati'].fillna(0) == 0) & (df['surface_terrain'].fillna(0) > 0)
    df.loc[mask_terrain, 'type_local'] = 'Terrain nu'
    df['type_local'] = df['type_local'].fillna('Autre/Dépendance')
    
    # Filter for 'Vente' only
    df = df[df['nature_mutation'].fillna('').str.upper() == 'VENTE']
    
    # Calculate Price per m²
    df['prix_m2'] = np.where(df['surface_reelle_bati'] > 0, df['valeur_fonciere'] / df['surface_reelle_bati'], np.nan)
    
    df['nombre_pieces_principales'] = pd.to_numeric(df['nombre_pieces_principales'], errors='coerce').fillna(0)
    
    return df

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6371 * c
    return km

def get_city_center(df, city_name):
    """Get the reference city's coordinates (mean of its data points)."""
    city_data = df[df['nom_commune'] == city_name]
    if not city_data.empty:
        center_lat = city_data['latitude'].mean()
        center_lon = city_data['longitude'].mean()
        if pd.notna(center_lat) and pd.notna(center_lon):
            return (center_lat, center_lon)
    return None

def filter_data_by_radius(df, center, radius_km):
    """Filter dataframe by radius around a center point."""
    if center is None:
        return df
    
    valid_coords = df.dropna(subset=['latitude', 'longitude']).copy()
    distances = haversine(center[0], center[1], valid_coords['latitude'], valid_coords['longitude'])
    return valid_coords[distances <= radius_km]

def get_estimation_stats(local_df, input_surface, input_terrain, is_terrain=False):
    """Calculates estimation statistics (median, q1, q3) based on local data."""
    if local_df.empty:
        return None
        
    df = local_df.copy()
    if is_terrain:
        df['prix_m2_calc'] = df['valeur_fonciere'] / df['surface_terrain'].replace(0, np.nan)
        surface_to_use = input_terrain
    else:
        df['prix_m2_calc'] = df['prix_m2']
        surface_to_use = input_surface
        
    median_m2 = df['prix_m2_calc'].median()
    q1_m2 = df['prix_m2_calc'].quantile(0.25)
    q3_m2 = df['prix_m2_calc'].quantile(0.75)
    
    return {
        'median': surface_to_use * median_m2,
        'low': surface_to_use * q1_m2,
        'high': surface_to_use * q3_m2,
        'median_m2': median_m2
    }
