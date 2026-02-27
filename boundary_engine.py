import os
import argparse
import logging
import requests
import pandas as pd
from shapely.geometry import LineString, MultiPolygon
from shapely.ops import polygonize, unary_union
import geopandas as gpd
try:
    from arcgis.gis import GIS
    from arcgis.gis import SharingLevel
    from arcgis.features import GeoAccessor
    from arcgis.geometry import Geometry
    ARCGIS_AVAILABLE = True
except ImportError:
    ARCGIS_AVAILABLE = False

# -------------------------------------------------
# LOGGING
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------------------------------
# GLOBAL CONFIG
# -------------------------------------------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# -------------------------------------------------
# WORLD REGIONS (UN-style macro grouping)
# -------------------------------------------------
REGIONS = {

    # -------------------------------------------------
    # EUROPE
    # -------------------------------------------------
    "northern_europe": {
        "IS": "Iceland", "NO": "Norway", "SE": "Sweden",
        "FI": "Finland", "DK": "Denmark", "IE": "Ireland",
        "GB": "United Kingdom", "EE": "Estonia",
        "LV": "Latvia", "LT": "Lithuania"
    },

    "western_europe": {
        "FR": "France", "DE": "Germany", "NL": "Netherlands",
        "BE": "Belgium", "LU": "Luxembourg",
        "CH": "Switzerland", "AT": "Austria"
    },

    "southern_europe": {
        "ES": "Spain", "PT": "Portugal", "IT": "Italy",
        "GR": "Greece", "MT": "Malta",
        "SI": "Slovenia", "HR": "Croatia",
        "BA": "Bosnia and Herzegovina",
        "RS": "Serbia", "ME": "Montenegro",
        "MK": "North Macedonia", "AL": "Albania"
    },

    "eastern_europe": {
        "PL": "Poland", "CZ": "Czech Republic",
        "SK": "Slovakia", "HU": "Hungary",
        "RO": "Romania", "BG": "Bulgaria",
        "UA": "Ukraine", "BY": "Belarus",
        "MD": "Moldova", "RU": "Russia"
    },

    # -------------------------------------------------
    # AFRICA
    # -------------------------------------------------
    "north_africa": {
        "MA": "Morocco", "DZ": "Algeria",
        "TN": "Tunisia", "LY": "Libya",
        "EG": "Egypt", "SD": "Sudan"
    },

    "west_africa": {
        "NG": "Nigeria", "GH": "Ghana", "SN": "Senegal",
        "ML": "Mali", "NE": "Niger", "BF": "Burkina Faso",
        "CI": "Côte d'Ivoire", "GW": "Guinea-Bissau",
        "GN": "Guinea", "SL": "Sierra Leone",
        "LR": "Liberia", "TG": "Togo",
        "BJ": "Benin", "GM": "Gambia",
        "MR": "Mauritania", "CV": "Cape Verde"
    },

    "central_africa": {
        "CM": "Cameroon", "CF": "Central African Republic",
        "TD": "Chad", "CG": "Republic of the Congo",
        "CD": "Democratic Republic of the Congo",
        "GQ": "Equatorial Guinea", "GA": "Gabon",
        "ST": "São Tomé and Príncipe"
    },

    "east_africa": {
        "ET": "Ethiopia", "KE": "Kenya",
        "UG": "Uganda", "TZ": "Tanzania",
        "RW": "Rwanda", "BI": "Burundi",
        "SO": "Somalia", "DJ": "Djibouti",
        "ER": "Eritrea", "SS": "South Sudan"
    },

    "southern_africa": {
        "ZA": "South Africa", "BW": "Botswana",
        "NA": "Namibia", "ZM": "Zambia",
        "ZW": "Zimbabwe", "MW": "Malawi",
        "MZ": "Mozambique", "LS": "Lesotho",
        "SZ": "Eswatini"
    },

    # -------------------------------------------------
    # ASIA
    # -------------------------------------------------
    "middle_east": {
        "IR": "Iran", "IQ": "Iraq", "SY": "Syria",
        "LB": "Lebanon", "IL": "Israel",
        "JO": "Jordan", "SA": "Saudi Arabia",
        "YE": "Yemen", "OM": "Oman",
        "AE": "United Arab Emirates",
        "QA": "Qatar", "KW": "Kuwait",
        "BH": "Bahrain", "TR": "Turkey"
    },

    "south_asia": {
        "AF": "Afghanistan", "PK": "Pakistan",
        "IN": "India", "BD": "Bangladesh",
        "NP": "Nepal", "BT": "Bhutan",
        "LK": "Sri Lanka", "MV": "Maldives"
    },

    "central_asia": {
        "KZ": "Kazakhstan", "UZ": "Uzbekistan",
        "TM": "Turkmenistan", "KG": "Kyrgyzstan",
        "TJ": "Tajikistan"
    },

    "east_asia": {
        "CN": "China", "JP": "Japan",
        "KR": "South Korea", "KP": "North Korea",
        "MN": "Mongolia"
    },

    "southeast_asia": {
        "TH": "Thailand", "VN": "Vietnam",
        "MY": "Malaysia", "SG": "Singapore",
        "ID": "Indonesia", "PH": "Philippines",
        "MM": "Myanmar", "KH": "Cambodia",
        "LA": "Laos", "BN": "Brunei",
        "TL": "Timor-Leste"
    },

    # -------------------------------------------------
    # AMERICAS
    # -------------------------------------------------
    "north_america": {
        "US": "United States", "CA": "Canada",
        "MX": "Mexico"
    },

    "central_america": {
        "GT": "Guatemala", "BZ": "Belize",
        "HN": "Honduras", "SV": "El Salvador",
        "NI": "Nicaragua", "CR": "Costa Rica",
        "PA": "Panama"
    },

    "caribbean": {
        "CU": "Cuba", "DO": "Dominican Republic",
        "HT": "Haiti", "JM": "Jamaica",
        "TT": "Trinidad and Tobago",
        "BB": "Barbados", "BS": "Bahamas"
    },

    "south_america": {
        "BR": "Brazil", "AR": "Argentina",
        "CL": "Chile", "PE": "Peru",
        "CO": "Colombia", "VE": "Venezuela",
        "UY": "Uruguay", "PY": "Paraguay",
        "BO": "Bolivia", "EC": "Ecuador",
        "GY": "Guyana", "SR": "Suriname"
    },

    # -------------------------------------------------
    # OCEANIA
    # -------------------------------------------------
    "australia_new_zealand": {
        "AU": "Australia", "NZ": "New Zealand"
    },

    "melanesia": {
        "PG": "Papua New Guinea",
        "FJ": "Fiji", "SB": "Solomon Islands",
        "VU": "Vanuatu"
    },

    "micronesia": {
        "FM": "Micronesia", "PW": "Palau",
        "MH": "Marshall Islands",
        "KI": "Kiribati", "NR": "Nauru"
    },

    "polynesia": {
        "WS": "Samoa", "TO": "Tonga",
        "TV": "Tuvalu"
    }
}

# -------------------------------------------------
# CLI ARGUMENTS
# -------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser(description="OSM Administrative Boundary Engine")

    parser.add_argument(
        "--regions",
        nargs="+",
        help="Regions to process (space separated)"
    )

    parser.add_argument(
        "--include",
        nargs="+",
        help="ISO country codes to force include"
    )

    parser.add_argument(
        "--exclude",
        nargs="+",
        help="ISO country codes to exclude"
    )

    parser.add_argument(
        "--mode",
        choices=["agol", "geopackage"],
        default="geopackage",
        help="Output mode: agol or geopackage"
    )
 
    args = parser.parse_args()

    if args.mode == "agol" and not ARCGIS_AVAILABLE:
        raise RuntimeError(
            "ArcGIS API is not installed in this environment. "
            "Use --mode geopackage or install arcgis."
        )
    return args

# -------------------------------------------------
# OVERPASS FETCH
# -------------------------------------------------
def fetch_admin_boundaries(iso_code):
    logging.info(f"Fetching OSM data for {iso_code}")
    all_elements = []

    for level in range(2, 12):
        query = f"""
        [out:json][timeout:300];
        area["ISO3166-1"="{iso_code}"][admin_level=2]->.searchArea;
        (
          relation["boundary"="administrative"]["admin_level"="{level}"](area.searchArea);
        );
        out geom;
        """

        try:
            r = requests.post(OVERPASS_URL, data=query, timeout=300)
            if r.status_code == 200:
                result = r.json()
                elements = result.get("elements", [])
                all_elements.extend(elements)
                logging.info(f"  level {level}: {len(elements)} relations")
        except Exception as e:
            logging.warning(f"Overpass failed for level {level}: {e}")

    return all_elements

# -------------------------------------------------
# BUILD POLYGONS
# -------------------------------------------------
def build_dataframe(elements):
    records = []

    for element in elements:
        if "members" not in element:
            continue

        lines = []
        for member in element["members"]:
            if member["type"] == "way" and "geometry" in member:
                coords = [(p["lon"], p["lat"]) for p in member["geometry"]]
                if len(coords) >= 2:
                    lines.append(LineString(coords))

        if not lines:
            continue

        try:
            merged = unary_union(lines)
            polygons = list(polygonize(merged))
            if not polygons:
                continue
            geom = MultiPolygon(polygons).buffer(0)
        except:
            continue

        tags = element.get("tags", {})

        records.append({
            "relation_id": element["id"],
            "name": tags.get("name"),
            "admin_level": tags.get("admin_level"),
            "geometry": geom
        })

    return pd.DataFrame(records)

# -------------------------------------------------
# SHAPELY TO ARCGIS
# -------------------------------------------------
def shapely_to_arcgis(geom):
    if geom is None or geom.is_empty:
        return None

    rings = []

    if geom.geom_type == "Polygon":
        polygons = [geom]
    else:
        polygons = list(geom.geoms)

    for poly in polygons:
        rings.append([list(coord) for coord in poly.exterior.coords])
        for interior in poly.interiors:
            rings.append([list(coord) for coord in interior.coords])

    return Geometry({
        "rings": rings,
        "spatialReference": {"wkid": 4326}
    })

# -------------------------------------------------
# MAIN ENGINE
# -------------------------------------------------
def main():

    args = parse_arguments()

    regions = args.regions or []
    include = args.include or []
    exclude = args.exclude or []
    mode = args.mode

    countries = {}

    if include:

        print("Include mode detected — ignoring region selection.")

        for iso_code in include:
            found = False

            for region_dict in REGIONS.values():
                if iso_code in region_dict:
                    countries[iso_code] = region_dict[iso_code]
                    found = True
                    break

            if not found:
                print(f"Warning: ISO code {iso_code} not found in REGIONS")

    else:
        # Normal region-based selection
        for region_name in regions:

            region_countries = REGIONS.get(region_name, {})

            for iso_code, country_name in region_countries.items():

                if iso_code in exclude:
                    continue

                countries[iso_code] = {
                    "name": country_name
                }

    if not countries:
        logging.info("No countries selected. Exiting.")
        return

    # Optional AGOL login
    if mode == "agol":
        portal_url = os.getenv("AGOL_PORTAL")
        username = os.getenv("AGOL_USERNAME")
        password = os.getenv("AGOL_PASSWORD")

        if not all([portal_url, username, password]):
            raise ValueError("Missing AGOL environment variables.")

        gis = GIS(portal_url, username, password)
        logging.info(f"Connected to {gis.properties.portalHostname}")

    # Process countries
    for iso_code, country_name in countries.items():

        logging.info(f"Processing {country_name}")

        elements = fetch_admin_boundaries(iso_code)
        if not elements:
            logging.warning(f"No data for {country_name}")
            continue

        df = build_dataframe(elements)

        if df.empty:
            logging.warning(f"No valid polygons built for {country_name}")
            continue

        if mode == "geopackage":

            gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
            filename = f"{country_name}_Admin_Boundaries.gpkg"
            gdf.to_file(filename, driver="GPKG")
            logging.info(f"Saved {filename}")

        elif mode == "agol":

            df["SHAPE"] = df["geometry"].apply(shapely_to_arcgis)
            df = df.dropna(subset=["SHAPE"])
            df_arc = df.drop(columns=["geometry"]).copy()

            sdf = GeoAccessor.from_df(df_arc, geometry_column="SHAPE")

            title = f"{country_name}_Admin_Boundaries"
            sdf.spatial.to_featurelayer(title=title, gis=gis)
            logging.info(f"Published {title}")

    logging.info("Run complete.")

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    main()