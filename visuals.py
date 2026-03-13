import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_map_fig(df, metric_col, metric_label, city_center, radius_km, zoom_level):
    """Generates the Mapbox scatter plot with the search radius circle."""
    map_draw_df = df.copy()
    
    # Configure map center
    center_coord = {"lat": city_center[0], "lon": city_center[1]} if city_center else {"lat": 46.22, "lon": 2.21}
    
    # Circle GeoJSON
    layers = []
    if city_center:
        angles = np.linspace(0, 2*np.pi, 100)
        R = 6371.0
        d_lat = radius_km / R
        d_lon = radius_km / (R * np.cos(np.pi * city_center[0] / 180.0))
        
        circle_lat = city_center[0] + np.degrees(d_lat * np.cos(angles))
        circle_lon = city_center[1] + np.degrees(d_lon * np.sin(angles))
        
        layers = [{
            "source": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[list(z) for z in zip(circle_lon, circle_lat)]]}
                }]
            },
            "type": "fill", "color": "rgba(255, 0, 0, 0.15)", "below": "traces"
        }, {
            "source": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature", "geometry": {"type": "LineString", "coordinates": [list(z) for z in zip(circle_lon, circle_lat)]}
                }]
            },
            "type": "line", "color": "red", "line": {"width": 2}
        }]

    max_val_map = map_draw_df[metric_col].quantile(0.95) if not map_draw_df.empty else 10000
    if max_val_map == 0 or np.isnan(max_val_map): max_val_map = 10000

    fig = px.scatter_mapbox(
        map_draw_df, lat="latitude", lon="longitude", color=metric_col,
        hover_name="nom_commune", opacity=0.35,
        hover_data={"latitude": False, "longitude": False, "valeur_fonciere": ":.0f", "prix_m2": ":.0f", "surface_reelle_bati": True, "surface_terrain": True, "type_local": True, "nombre_pieces_principales": True},
        color_continuous_scale="Plasma", range_color=[0, max_val_map],
        zoom=zoom_level, center=center_coord, height=600, labels={metric_col: metric_label}
    )
    fig.update_layout(mapbox_style="open-street-map", mapbox_layers=layers, margin={"r":0,"t":0,"l":0,"b":0})
    return fig

def create_correlation_heatmap(corr_matrix):
    """Creates an interactive heatmap for the correlation matrix."""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=['Prix', 'Surface Habitable', 'Surface Terrain'],
        y=['Prix', 'Surface Habitable', 'Surface Terrain'],
        colorscale='Viridis',
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}", hoverinfo="text"
    ))
    fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10), height=350,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_scatter_plot(df, x_col, y_col, color_col, x_label, y_label):
    """Creates a basic scatter plot with styling."""
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col, opacity=0.5,
        labels={x_col: x_label, y_col: y_label, color_col: 'Type de Bien'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_pie_chart(labels, values):
    """Creates a simple pie chart."""
    fig = px.pie(names=labels, values=values, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
    return fig

def create_bar_chart(x, y, x_label, y_label, colors):
    """Creates a bar chart with labels outside."""
    fig = px.bar(x=x, y=y, labels={'x': x_label, 'y': y_label}, color=colors, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(texttemplate='%{y:,.0f} €', textposition='outside')
    fig.update_layout(height=400, showlegend=False, margin=dict(t=20, b=20))
    return fig

def create_boxplot(df, x_col, y_col, color_col, x_label, y_label, category_orders):
    """Creates a box plot for typology distribution."""
    fig = px.box(
        df, x=x_col, y=y_col, color=color_col,
        category_orders=category_orders,
        labels={x_col: x_label, y_col: y_label},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(height=450)
    return fig

def create_dist_histogram(df, x_col, x_label, title, median_val=None):
    """Creates a distribution histogram with a median line."""
    fig = px.histogram(
        df, x=x_col, nbins=50,
        labels={x_col: x_label, 'count': 'Nombre de ventes'},
        color_discrete_sequence=['#636EFA'], title=title
    )
    if median_val is not None:
        fig.add_vline(x=median_val, line_dash="dash", line_color="red", annotation_text="Prix Médian Estimé")
    fig.update_layout(height=400, margin=dict(t=50, b=20, l=20, r=20))
    return fig
