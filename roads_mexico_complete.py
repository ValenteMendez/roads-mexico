#!/usr/bin/env python3
# roads_states_complete.py
# Fetch & map roads for all 32 Mexican states using OSMnx boundaries.
# • Default: small buffer to capture fringe roads, then clip back.
# • Jalisco & Tabasco: larger buffer (0.1°) before clipping, to catch all edge roads.
# • Colima: drop tiny offshore islets via largest‐polygon.
# • Remove any Point geometries after clipping.
# • No titles on the map itself. Outputs three maps per state in ./output:
#     basic_<code>_<state>.png
#     typemap_<code>_<state>.png
#     distmap_<code>_<state>.png

import os
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import MultiPolygon

os.makedirs("output", exist_ok=True)

def largest_polygon(geom):
    if isinstance(geom, MultiPolygon):
        return max(geom.geoms, key=lambda g: g.area)
    return geom

# road type hierarchy + colormap
highway_order = [
    'motorway','trunk','primary','secondary',
    'tertiary','unclassified','residential','service'
]
cmap = plt.cm.get_cmap('inferno_r', len(highway_order)+1)

def get_hwy_code(hw):
    hw0 = hw[0] if isinstance(hw, list) else hw
    return highway_order.index(hw0) if hw0 in highway_order else len(highway_order)

# INEGI codes & state names
states = [
    ('01','Aguascalientes'),('02','Baja California'),('03','Baja California Sur'),
    ('04','Campeche'),('05','Coahuila'),('06','Colima'),('07','Chiapas'),
    ('08','Chihuahua'),('09','Mexico City'),('10','Durango'),('11','Guanajuato'),
    ('12','Guerrero'),('13','Hidalgo'),('14','Jalisco'),('15','Estado de México'),
    ('16','Michoacán'),('17','Morelos'),('18','Nayarit'),('19','Nuevo León'),
    ('20','Oaxaca'),('21','Puebla'),('22','Querétaro'),('23','Quintana Roo'),
    ('24','San Luis Potosí'),('25','Sinaloa'),('26','Sonora'),('27','Tabasco'),
    ('28','Tamaulipas'),('29','Tlaxcala'),('30','Veracruz'),
    ('31','Yucatán'),('32','Zacatecas'),
]

# default small buffer (~0.02° ≈ 2 km)
BUFFER_DEG = 0.02
# special large buffer for problematic states
SPECIAL_BUFFER = 0.1
SPECIAL_STATES = {"Jalisco", "Tabasco"}

for code, name in states:
    print(f"▶ Processing {code} — {name}")
    # 1. get raw OSMnx boundary (EPSG:4326)
    gdf = ox.geocode_to_gdf(f"{name}, Mexico")
    raw_geom = gdf.geometry.iloc[0]

    # 2. for Colima, drop tiny islets
    if name == "Colima":
        clean_geom = largest_polygon(raw_geom)
    else:
        clean_geom = raw_geom

    # 3. choose buffer size
    buf = SPECIAL_BUFFER if name in SPECIAL_STATES else BUFFER_DEG
    fetch_geom = clean_geom.buffer(buf)

    # 4. fetch & project roads
    G = ox.graph_from_polygon(fetch_geom, network_type="drive", simplify=True)
    roads = ox.graph_to_gdfs(G, nodes=False, edges=True).to_crs(epsg=3857)

    # 5. clip back to true boundary and drop stray Points
    boundary_proj = gpd.GeoSeries([clean_geom], crs="EPSG:4326") \
                     .to_crs(epsg=3857).iloc[0]
    roads = gpd.clip(roads, boundary_proj)
    roads = roads[roads.geom_type.str.contains("Line")].copy()

    # 6. encode highway types and compute widths
    roads['hwy_code'] = roads['highway'].apply(get_hwy_code)
    center = boundary_proj.centroid
    roads['dist'] = roads.geometry.distance(center)
    raw_lw = 1 / np.exp(roads['dist'] / 1e6)
    mn, mx = raw_lw.min(), raw_lw.max()
    roads['lw'] = 0.05 + (raw_lw - mn) / (mx - mn) * (0.9 - 0.05)

    # 7. compute plot extent (+5% buffer)
    x0, y0, x1, y1 = boundary_proj.bounds
    dx, dy = 0.05 * (x1 - x0), 0.05 * (y1 - y0)
    extent = (x0 - dx, x1 + dx, y0 - dy, y1 + dy)

    # safe filename
    safe = (name.lower()
            .replace(' ','_')
            .replace('á','a').replace('é','e')
            .replace('í','i').replace('ó','o')
            .replace('ú','u').replace('ñ','n'))

    # ---- Map 1: basic ----
    fig, ax = plt.subplots(figsize=(8,8), facecolor='white')
    roads.plot(ax=ax, color='black', linewidth=0.05)
    gpd.GeoSeries([boundary_proj]).boundary.plot(
        ax=ax, color='black', linewidth=0.5)
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_axis_off()
    fig.savefig(f"output/basic_{code}_{safe}.png", dpi=300)
    plt.close(fig)

    # ---- Map 2: type ----
    fig, ax = plt.subplots(figsize=(8,8), facecolor='#090909')
    roads.plot(ax=ax, column='hwy_code', cmap=cmap,
               linewidth=0.05, alpha=0.8, legend=False)
    gpd.GeoSeries([boundary_proj]).boundary.plot(
        ax=ax, color='white', linewidth=0.5)
    patches = [plt.matplotlib.patches.Patch(
                   color=cmap(i), label=highway_order[i])
               for i in range(len(highway_order))]
    patches.append(plt.matplotlib.patches.Patch(
        color=cmap(len(highway_order)), label='other'))
    ax.legend(handles=patches, title='Road type',
              loc='lower left', bbox_to_anchor=(0.02,0.02),
              facecolor='#222222', edgecolor='white', labelcolor='white')
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_axis_off()
    fig.savefig(f"output/typemap_{code}_{safe}.png", dpi=300)
    plt.close(fig)

    # ---- Map 3: distance-scaled ----
    fig, ax = plt.subplots(figsize=(8,8), facecolor='#090909')
    roads.plot(ax=ax, column='hwy_code', cmap=cmap,
               linewidth=roads['lw'], alpha=0.8, legend=False)
    gpd.GeoSeries([boundary_proj]).boundary.plot(
        ax=ax, color='white', linewidth=0.5)
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_axis_off()
    fig.savefig(f"output/distmap_{code}_{safe}.png", dpi=300)
    plt.close(fig)

print("✅ All 32 states processed with correct Jalisco, Tabasco (and Colima) handling.")
