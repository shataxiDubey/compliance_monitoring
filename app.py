import rasterio.plot
import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import itertools
from scipy.spatial import cKDTree
import geopy.distance
import matplotlib.pyplot as plt
from operator import itemgetter
import rasterio
from pyproj import Transformer
from shapely.geometry import box
from rasterio.mask import mask

# Title of the app
st.title("Automatic Compliance Monitoring for Brick Kilns")

# Create two columns with a 40% - 60% split
col1, col2 = st.columns([0.35, 0.65])
@st.cache_data
def plot_raster_with_data(tif_file, brick_kilns, _bbox):
    """
    Plots a raster image from a TIFF file using a bounding box.
    """
    with rasterio.open(tif_file) as src:
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Create a GeoDataFrame with the bounding box
        geo = gpd.GeoDataFrame({'geometry': [_bbox]}, crs=src.crs)
        
        # Crop the raster
        out_image, out_transform = mask(src, geo.geometry, crop=True)
        
        # Update metadata
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        # Plot the cropped image
        if out_image.any():
            # brick_kilns_compliant = brick_kilns[brick_kilns['compliant']]
            # ax.scatter(brick_kilns_compliant['lon'], brick_kilns_compliant['lat'], color='green', s=10, marker='o', label='Compliant Brick Kilns')
            # brick_kilns_non_compliant = brick_kilns[~brick_kilns['compliant']]
            # ax.scatter(brick_kilns_non_compliant['lon'], brick_kilns_non_compliant['lat'], color='red', s=10, marker='o', label='Non-compliant Brick Kilns')
            
            rasterio.plot.show(out_image, ax=ax, cmap='gray', alpha = 0.2)
            ax.set_title("Cropped TIF Image")
            ax.axis('off')
        else:
            st.error("No data within the specified bounding box.")
            return
        
        brick_kilns = gpd.GeoDataFrame(brick_kilns, geometry=gpd.points_from_xy(brick_kilns.lon, brick_kilns.lat), crs="EPSG:4326")

        brick_kilns_compliant = brick_kilns[brick_kilns['compliant']]
        ax.scatter(brick_kilns_compliant.geometry.x, brick_kilns_compliant.geometry.y, color='green', s=10, marker='o', label='Compliant Brick Kilns', zorder=20)

        # Plot non-compliant brick kilns in red
        brick_kilns_non_compliant = brick_kilns[~brick_kilns['compliant']]
        ax.scatter(brick_kilns_non_compliant.geometry.x, brick_kilns_non_compliant.geometry.y, color='red', s=10, marker='o', label='Non-Compliant Brick Kilns', zorder=20)
        
        # Display the plot in Streamlit
        st.pyplot(fig)

@st.cache_data
def create_bbox_from_coordinates(tif_file, min_lon, min_lat, max_lon, max_lat):
    """
    Creates a bounding box from given coordinates transformed to the raster's CRS.
    """
    with rasterio.open(tif_file) as src:
        raster_crs = src.crs
        transformer = Transformer.from_crs("epsg:4326", raster_crs, always_xy=True)
        min_x, min_y = transformer.transform(min_lon, min_lat)
        max_x, max_y = transformer.transform(max_lon, max_lat)
        
    bbox = box(min_x, min_y, max_x, max_y)
    return bbox

@st.cache_data
def read_csv(file):
    return pd.read_csv(file)

@st.cache_data
def read_geopandas(file):
    return gpd.read_file(file)

fp2 = 'India_State_Boundary.shp'
data2 = read_geopandas(fp2)

waterways_path = 'waterways.shp'
waterways = read_geopandas(waterways_path)

tif_file = 'landscan-global-2022-colorized.tif'

# Load brick kilns data
brick_kilns_paths = {
    'All' : 'combined_file.csv',
    "Punjab": 'punjab.csv',
    "Haryana": 'haryana.csv',
    "Bihar": 'bihar.csv',
    "Uttar Pradesh": 'uttar_pradesh.csv',
    "West Bengal": 'west_bengal.csv',
}

@st.cache_data
def plot_fig(state, brick_kilns):
    fig, ax = plt.subplots(figsize=(10, 6))
    data2.plot(ax=ax, cmap='Pastel2', edgecolor='black', linewidth=0.1)  # State map
    waterways.plot(ax=ax, color='blue', linewidth=0.2)  # Water bodies
    brick_kilns_compliant = brick_kilns[brick_kilns['compliant']]
    ax.scatter(brick_kilns_compliant['lon'], brick_kilns_compliant['lat'], color='green', s=10, marker='o', label='Compliant Brick Kilns')

    # Plot non-compliant brick kilns in red
    brick_kilns_non_compliant = brick_kilns[~brick_kilns['compliant']]
    ax.scatter(brick_kilns_non_compliant['lon'], brick_kilns_non_compliant['lat'], color='red', s=10, marker='o', label='Non-compliant Brick Kilns')

    if state == 'All': #(plot india map)
        ax.set_xlim(66, 98)
        ax.set_ylim(7, 38)
    elif state == 'Bihar':
        ax.text(83, 25.8, 'Uttar\n Pradesh')
        ax.text(85.5, 25.5, 'Bihar')
        ax.text(87.9, 25.3, 'West\n Bengal')
        ax.set_xlim(83, 88.6)
        ax.set_ylim(24.25, 27.53)
    elif state == 'Haryana':
        ax.text(77.3, 29.5, 'Uttar \nPradesh')
        ax.text(74.5, 28.5, 'Rajasthan')
        ax.text(75.7, 30.7, 'Punjab')
        ax.text(76.2, 29.4, 'Haryana')
        ax.set_xlim(74.2, 78.1)
        ax.set_ylim(27.6, 31)
    elif state == 'Punjab':
        ax.text(76.3, 31.5, 'Himachal Pradesh')
        ax.text(75, 30.8, 'Punjab')
        ax.text(74.3, 30.4, 'Haryana')
        ax.set_xlim(73.8, 77)
        ax.set_ylim(29.5, 32.6)
    elif state == 'Uttar Pradesh':
        ax.text(76.3, 31.5, 'Himachal Pradesh')
        ax.text(75, 30.8, 'Punjab')
        ax.text(74.3, 30.4, 'Haryana')
        ax.set_xlim(76, 85)
        ax.set_ylim(23.6, 31)
    elif state == 'West Bengal':
        ax.set_xlim(85.7, 90)
        ax.set_ylim(21.3, 27.5)

    plt.legend()
    plt.title(f"{state} Brick Kilns Compliance")
    st.pyplot(fig)

with col1:
    # Dropdown for selecting the state
    # state = st.selectbox("Select State", ["Punjab", "Haryana", "Bihar"])  # Update the list as needed
    state = st.selectbox("Select State", ["All", "Punjab", "Haryana", "Bihar", "West Bengal", "Uttar Pradesh"])  # Update the list as needed

    # Checkboxes for different compliance criteria
    distance_kilns = st.checkbox("Inter-brick kiln distance < 1km")
    distance_hospitals = st.checkbox("Distance to Hospitals < 800m")
    distance_water_bodies = st.checkbox("Distance to Water bodies < 500m")

     # Add a horizontal line to separate sections
    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("Show Population Density")
    population_density = False

    population_density = st.checkbox("Yes")
        
with col2:
    # Load brick kilns data for the selected state
    brick_kilns_path = brick_kilns_paths[state]
    brick_kilns = read_csv(brick_kilns_path)

    brick_kilns['compliant'] = True
    if distance_kilns:
        bk_kiln_mapping = read_csv(f'./brick_kiln_bk_dist/{state}_bk_bk_dist.csv')
        brick_kilns['compliant'] &= bk_kiln_mapping['dist'] >= 1
    if distance_hospitals:
        bk_hospital_mapping = read_csv(f'./brick_kiln_hospital_dist/{state}_bk_hospital_dist.csv')
        brick_kilns['compliant'] &= bk_hospital_mapping['distance_km'] >= 0.8
    if distance_water_bodies:
        bk_river_mapping = read_csv(f'./brick_kiln_river_dist/{state}_bk_river_distance.csv')
        brick_kilns['compliant'] &= bk_river_mapping['distance'] >= 0.5

    # Plotting the results
    if (population_density == False):
        plot_fig(state, brick_kilns)
        brick_kilns_non_compliant = brick_kilns[~brick_kilns['compliant']]

    else:
        brick_kilns_non_compliant = brick_kilns[~brick_kilns['compliant']]
        
        if state == 'All':
            bbox1 = create_bbox_from_coordinates(tif_file, min_lon= 60.0, max_lon=98.0, min_lat=7.0, max_lat=48.0 )
            plot_raster_with_data(tif_file, brick_kilns, bbox1)

    
    # Display the number of non-compliant kilns
    num_brick_kilns = len(brick_kilns)
    st.markdown(f"""
        <div style="text-align: center; font-size: 18px;">
            Number of brick kilns: {num_brick_kilns}
        </div>
    """, unsafe_allow_html=True)

    num_non_compliant = len(brick_kilns_non_compliant)
    st.markdown(f"""
        <div style="text-align: center; font-size: 18px;">
            Number of non-compliant brick kilns: {num_non_compliant}
        </div>
    """, unsafe_allow_html=True)