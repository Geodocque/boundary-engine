# 🌍 Boundary Engine

A command-line tool to extract administrative boundaries from
OpenStreetMap (via Overpass API) and export them as:

-   📦 GeoPackage files (.gpkg)
-   ☁️ Hosted Feature Layers in ArcGIS Online

Designed for scalable regional batch processing and enterprise
publishing workflows.

------------------------------------------------------------------------

## 🚀 Features

-   Fetches administrative boundary levels 2--11
-   Builds topology-correct polygons from OSM relations
-   Region-based country selection
-   ISO include / exclude overrides
-   Dual output modes:
    -   `geopackage`
    -   `agol`
-   Secure AGOL authentication via environment variables
-   Clean logging output
-   GitHub-ready structure

------------------------------------------------------------------------

## 📦 Installation

### 1️⃣ Clone the repository

``` bash
git clone https://github.com/Geodocque/boundary-engine.git
cd boundary-engine
```

### 2️⃣ Create Conda environment

``` bash
conda env create -f environment.yml
conda activate boundary_engine
```

------------------------------------------------------------------------

## 🖥 Usage

### 🔹 Export GeoPackage (Open-Source Mode)

Export all West African countries:

``` bash
python boundary_engine.py --regions west_africa --mode geopackage
```

Export only Togo:

``` bash
python boundary_engine.py --include TG --mode geopackage
```

Export multiple specific countries:

``` bash
python boundary_engine.py --include TG GH NG --mode geopackage
```

This creates files like:

    Togo_Admin_Boundaries.gpkg
    Ghana_Admin_Boundaries.gpkg

------------------------------------------------------------------------

### 🔹 Publish Hosted Feature Layer to ArcGIS Online

First set environment variables:

#### Windows

``` bash
set AGOL_PORTAL=https://yourportal.maps.arcgis.com/
set AGOL_USERNAME=your_username
set AGOL_PASSWORD=your_password
```

#### macOS / Linux

``` bash
export AGOL_PORTAL=https://yourportal.maps.arcgis.com/
export AGOL_USERNAME=your_username
export AGOL_PASSWORD=your_password
```

Then run:

``` bash
python boundary_engine.py --include TG --mode agol
```

Publish an entire region:

``` bash
python boundary_engine.py --regions west_africa --mode agol
```

------------------------------------------------------------------------

## 🌎 Region System

Countries are grouped into world regions.

Examples:

``` bash
--regions west_africa
--regions middle_east
--regions south_asia
```

Exclude specific countries:

``` bash
python boundary_engine.py --regions west_africa --exclude NG GH --mode geopackage
```

If `--include` is used, region selection is ignored.

------------------------------------------------------------------------

## ⚙️ Modes

### `--mode geopackage`

-   No ArcGIS dependency required
-   Exports GeoPackage locally
-   Open-source compatible

### `--mode agol`

-   Requires ArcGIS API for Python
-   Publishes Hosted Feature Layers
-   Uses environment variables for login
-   No credentials stored in script

------------------------------------------------------------------------

## 🧠 How It Works

1.  Queries Overpass API for each admin level
2.  Reconstructs polygons from OSM relation members
3.  Fixes topology using unary union + polygonize
4.  Exports via:
    -   GeoPandas → GeoPackage
    -   ArcGIS API → Hosted Feature Layer

------------------------------------------------------------------------

## 📊 Output Structure

Each boundary contains:

-   relation_id
-   name
-   name_en
-   admin_level
-   boundary
-   type
-   wikidata

CRS: WGS84 (EPSG:4326)

------------------------------------------------------------------------

## ⚠️ Notes

-   Overpass API can be inconsistent; rerunning may retrieve additional
    relations.
-   Large countries may take longer to process.
-   AGOL mode requires ArcGIS Pro clone environment or arcgis Python
    package installed.

------------------------------------------------------------------------

## 📜 License

MIT License

------------------------------------------------------------------------

## 👤 Author

Built as a scalable administrative boundary ingestion engine\
for enterprise and open geospatial workflows.
