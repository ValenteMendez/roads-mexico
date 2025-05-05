# Mexican Roads Mapper

A Python script to generate beautiful road network visualizations for all 32 Mexican states.

## Overview

`roads_mexico_complete.py` fetches road data from OpenStreetMap and creates three visualization maps for each Mexican state:

- **Basic map**: Simple black and white road network
- **Type map**: Color-coded by road type (motorway, trunk, primary, etc.)
- **Distance map**: Roads thickness varies based on distance from state center

## Requirements

- Python 3.x
- Libraries: osmnx, geopandas, matplotlib, numpy, shapely

## Usage

Simply run the script:

```bash
python roads_mexico_complete.py
```

## Output

The script creates an `output` directory containing three maps per state (96 maps total):

- `basic_<code>_<state>.png`: Black and white road network
- `typemap_<code>_<state>.png`: Color-coded by road hierarchy
- `distmap_<code>_<state>.png`: Distance-weighted visualization

## Special Handling

- Jalisco & Tabasco: Uses larger buffer (0.1°) to capture edge roads
- Colima: Drops tiny offshore islets
- All states: Removes point geometries after clipping 