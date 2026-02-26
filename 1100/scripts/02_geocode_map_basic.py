# =============================================================================
# SCRIPT 2 — Section 1100: Geocode Taco Shops & Create a Basic Map
# =============================================================================
# WHAT THIS SCRIPT DOES:
#   1. Reads the taco shop CSV created by Script 1
#   2. Sends each address to the Mapbox Geocoding API to get lat/lon coordinates
#   3. Saves the enriched data (with lat/lon) as a new CSV
#   4. Creates an interactive web map with a basic OpenStreetMap basemap
#   5. Saves the map as an HTML file ready to open in a browser
#
# BEFORE YOU RUN:
#   - Add your Mapbox access token (see Step 2 below)
#   - Make sure Script 1 has been run (data/fw_tacos.csv must exist)
#
# OUTPUT:
#   data/fw_tacos_geocoded.csv
#   data/fw_tacos_map_basic.html
#
# TO RUN:
#   python scripts/02_geocode_map_basic.py
# =============================================================================


# =============================================================================
# STEP 1: IMPORT LIBRARIES
# =============================================================================

import requests         # For sending API calls to Mapbox
import pandas as pd     # For reading and working with tabular data
import folium           # For creating interactive HTML maps
import os               # For file/folder path operations
import time             # For pausing between API calls


# =============================================================================
# STEP 2: ADD YOUR MAPBOX ACCESS TOKEN
# =============================================================================
# HOW TO FIND YOUR TOKEN:
#   1. Go to https://account.mapbox.com/access-tokens/
#   2. Sign in to your Mapbox account
#   3. Copy your "Default public token" (starts with "pk.")
#   4. Paste it below, replacing the placeholder text

MAPBOX_TOKEN = "pk.eyJ1IjoibWFyaXNzYWhvdWZmIiwiYSI6ImNtbHRxbnZyNzAzOXMzZ3EwaTk3dGI3N2YifQ.G7G7J7DyAWWxdslqbPvkmg"

if MAPBOX_TOKEN == "PASTE_YOUR_MAPBOX_TOKEN_HERE":
    print("ERROR: You need to add your Mapbox access token!")
    print("  Open this script and replace PASTE_YOUR_MAPBOX_TOKEN_HERE")
    print("  with your real token from: https://account.mapbox.com/access-tokens/")
    exit()


# =============================================================================
# STEP 3: DEFINE THE GEOCODING FUNCTION
# =============================================================================
# This function takes an address string and returns lat/lon coordinates.
# It uses the Mapbox Forward Geocoding API (v6).

def geocode_address(address_string, token):
    """
    Convert a text address into [latitude, longitude] coordinates.

    Parameters:
        address_string (str): Full address to geocode
        token (str): Mapbox public access token

    Returns:
        tuple: (latitude, longitude) as floats, or (None, None) on failure
    """

    if not address_string or not address_string.strip():
        return None, None

    # Build the API endpoint URL.
    # requests.utils.quote() URL-encodes the address — this converts spaces to
    # %20, commas to %2C, etc., so the address can be safely included in a URL.
    geocode_url = (
        f"https://api.mapbox.com/search/geocode/v6/forward"
        f"?q={requests.utils.quote(address_string)}"
        f"&country=us"       # Limit results to the US
        f"&limit=1"          # Return only the top result
        f"&access_token={token}"
    )

    try:
        response = requests.get(geocode_url, timeout=10)

        if response.status_code != 200:
            return None, None

        # response.json() parses the JSON response string into a Python dictionary
        data = response.json()

        # Extract the coordinates from the first (best) feature result.
        # GeoJSON format: coordinates are [longitude, latitude] — note the order!
        # (In most contexts we say "lat, lon" but GeoJSON reverses this to "lon, lat")
        features = data.get("features", [])
        if features:
            coords = features[0]["geometry"]["coordinates"]
            lon = coords[0]
            lat = coords[1]
            return lat, lon

    except requests.exceptions.RequestException:
        return None, None

    return None, None


# =============================================================================
# STEP 4: READ THE TACO SHOP DATA
# =============================================================================
print("=" * 60)
print("  Fort Worth Taco Geocoder & Basic Map Builder")
print("=" * 60)

input_path = os.path.join("data", "fw_tacos.csv")

if not os.path.exists(input_path):
    print(f"\nERROR: File not found: {input_path}")
    print("Please run Script 1 first (01_scrape_fw_tacos.py)")
    exit()

df = pd.read_csv(input_path)
print(f"\nLoaded {len(df)} taco shops from: {input_path}")


# =============================================================================
# STEP 5: GEOCODE EACH ADDRESS
# =============================================================================
print("\nGeocoding addresses using the Mapbox API...")

latitudes = []
longitudes = []

for i, row in df.iterrows():
    address = row.get("Address", "")
    name = row.get("Name", f"Row {i}")
    print(f"  [{i+1}/{len(df)}] {name[:45]}...")

    lat, lon = geocode_address(address, MAPBOX_TOKEN)
    latitudes.append(lat)
    longitudes.append(lon)

    # Short pause between requests (good API citizenship)
    time.sleep(0.1)

df["Latitude"] = latitudes
df["Longitude"] = longitudes

geocoded_count = df["Latitude"].notna().sum()
print(f"\nSuccessfully geocoded: {geocoded_count} of {len(df)} addresses")


# =============================================================================
# STEP 6: SAVE GEOCODED DATA
# =============================================================================
os.makedirs("data", exist_ok=True)
geocoded_path = os.path.join("data", "fw_tacos_geocoded.csv")
df.to_csv(geocoded_path, index=False, encoding="utf-8-sig")
print(f"Geocoded data saved to: {geocoded_path}")


# =============================================================================
# STEP 7: CREATE THE INTERACTIVE MAP
# =============================================================================
print("\nBuilding interactive map with Folium...")

df_mapped = df.dropna(subset=["Latitude", "Longitude"]).copy()
print(f"  Placing {len(df_mapped)} markers on the map.")

# Fort Worth city center coordinates — used as the default map center
# (We also compute the mean from our data as a fallback)
if len(df_mapped) > 0:
    center_lat = df_mapped["Latitude"].mean()
    center_lon = df_mapped["Longitude"].mean()
else:
    # Fallback: downtown Fort Worth
    center_lat = 32.7555
    center_lon = -97.3308

# Create the base map centered on Fort Worth
fw_map = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12,
    tiles="OpenStreetMap"
)

# --- Map Title ---
title_html = """
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
     z-index: 1000; background-color: white; padding: 10px 20px;
     border: 2px solid #4D1979; border-radius: 8px; font-family: Georgia, serif;
     font-size: 16px; font-weight: bold; color: #4D1979; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    🌮 Best Tacos in Fort Worth
</div>
"""
fw_map.get_root().html.add_child(folium.Element(title_html))

# --- Define Colors by Neighborhood ---
# Using different marker colors per neighborhood helps readers understand
# the geographic distribution of the data.
# Folium accepts these named colors for icon markers:
# red, blue, green, purple, orange, darkred, lightred, beige, darkblue,
# darkgreen, cadetblue, darkpurple, white, pink, lightblue, lightgreen,
# gray, black, lightgray

NEIGHBORHOOD_COLORS = {
    "Stockyards": "darkred",
    "Near Northside": "red",
    "Near Southside": "orange",
    "West 7th (Cultural District)": "purple",
    "West 7th": "purple",
    "Hulen / Cityview": "darkblue",
    "Camp Bowie West": "green",
    "Ridglea": "darkgreen",
    "River Oaks": "cadetblue",
    "Default": "gray"
}

# --- Add Markers ---
for i, row in df_mapped.iterrows():

    # Look up the color for this neighborhood (use gray if not in our dict)
    neighborhood = row.get("Neighborhood", "")
    marker_color = NEIGHBORHOOD_COLORS.get(neighborhood, NEIGHBORHOOD_COLORS["Default"])

    # Build the popup content
    description = row.get("Description", "")
    specialty = row.get("Specialty", "")

    popup_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 13px; min-width: 220px; max-width: 300px;">
        <h4 style="margin: 0 0 6px 0; color: #4D1979; border-bottom: 1px solid #ccc; padding-bottom: 4px;">
            {row['Name']}
        </h4>
        <b>📍 {row.get('Address', '')}</b><br>
        <i style="color: #666;">{neighborhood}</i><br><br>
        <b>Known for:</b> {specialty}<br><br>
        <span style="font-size: 12px;">{description}</span>
    </div>
    """

    # folium.Marker() places a standard pin icon on the map.
    # folium.Icon() lets us customize the pin's color.
    # prefix="fa" uses Font Awesome icons — "utensils" is a fork-and-knife icon.
    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=f"🌮 {row['Name']}",
        icon=folium.Icon(color=marker_color, icon="cutlery", prefix="fa")
    ).add_to(fw_map)

# --- Add a Legend ---
# This explains what each marker color means
legend_html = """
<div style="position: fixed; bottom: 30px; left: 20px; z-index: 1000;
     background-color: white; padding: 12px; border: 2px solid #4D1979;
     border-radius: 8px; font-family: Arial, sans-serif; font-size: 12px;">
    <b style="color: #4D1979;">Neighborhoods</b><br>
    <span style="color: darkred;">&#9679;</span> Stockyards / Near Northside<br>
    <span style="color: orange;">&#9679;</span> Near Southside<br>
    <span style="color: purple;">&#9679;</span> West 7th / Cultural District<br>
    <span style="color: darkblue;">&#9679;</span> Hulen / Cityview<br>
    <span style="color: green;">&#9679;</span> Camp Bowie / Ridglea<br>
    <span style="color: cadetblue;">&#9679;</span> River Oaks<br>
</div>
"""
fw_map.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl().add_to(fw_map)


# =============================================================================
# STEP 8: SAVE THE MAP
# =============================================================================
map_output_path = os.path.join("data", "fw_tacos_map_basic.html")
fw_map.save(map_output_path)

print(f"  Map saved to: {map_output_path}")
print("\n" + "=" * 60)
print("  SCRIPT COMPLETE!")
print("=" * 60)
print(f"\nOpen in browser: {map_output_path}")
print("\nNext: Follow Step 4 in instructions to create your custom TCU-themed")
print("  Mapbox style, then run Script 3.")
