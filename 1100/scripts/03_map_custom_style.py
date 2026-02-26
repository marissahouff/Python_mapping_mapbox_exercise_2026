# =============================================================================
# SCRIPT 3 — Section 1100: Create Map with Custom TCU-Themed Mapbox Style
# =============================================================================
# WHAT THIS SCRIPT DOES:
#   Recreates the interactive taco map from Script 2, but replaces the plain
#   OpenStreetMap basemap with your custom Mapbox style — designed in the
#   TCU color palette (deep purple, white, charcoal, with minor red accents).
#
# BEFORE YOU RUN:
#   1. Complete Step 4 in the instructions (build your custom Mapbox style)
#   2. Publish the style and copy your Style URL
#   3. Fill in MAPBOX_TOKEN and MAPBOX_STYLE_URL below
#   4. Script 2 must have been run (data/fw_tacos_geocoded.csv must exist)
#
# OUTPUT:
#   data/fw_tacos_map_custom.html
#
# TO RUN:
#   python scripts/03_map_custom_style.py
# =============================================================================


# =============================================================================
# STEP 1: IMPORT LIBRARIES
# =============================================================================

import pandas as pd
import folium
import os


# =============================================================================
# STEP 2: ADD YOUR MAPBOX CREDENTIALS
# =============================================================================

# --- A) Your Mapbox Public Access Token ---
# Starts with "pk." — found at: https://account.mapbox.com/access-tokens/
MAPBOX_TOKEN = "pk.eyJ1IjoibWFyaXNzYWhvdWZmIiwiYSI6ImNtbHRxbnZyNzAzOXMzZ3EwaTk3dGI3N2YifQ.G7G7J7DyAWWxdslqbPvkmg"

# --- B) Your Mapbox Style URL ---
# Using Mapbox's built-in "Streets" style (dark theme)
MAPBOX_STYLE_URL = "mapbox://styles/mapbox/streets-v12"

# --- Validation ---
if MAPBOX_TOKEN == "PASTE_YOUR_MAPBOX_TOKEN_HERE":
    print("ERROR: Add your Mapbox access token to the MAPBOX_TOKEN variable.")
    exit()

if "YOUR_USERNAME" in MAPBOX_STYLE_URL or "YOUR_STYLE_ID" in MAPBOX_STYLE_URL:
    print("ERROR: Add your Mapbox Style URL to the MAPBOX_STYLE_URL variable.")
    print("  Example: mapbox://styles/johndoe/clxabcdefg1234")
    exit()


# =============================================================================
# STEP 3: BUILD THE MAPBOX TILE URL
# =============================================================================
# Mapbox style URLs (mapbox://styles/...) must be converted to HTTP tile URLs
# before Folium can use them to load map tiles.
#
# The tile URL pattern for Mapbox Styles API is:
#   https://api.mapbox.com/styles/v1/{username}/{styleid}/tiles/256/{z}/{x}/{y}@2x?access_token={token}
#
# We parse the username and style ID out of our Mapbox style URL to build this.

style_path = MAPBOX_STYLE_URL.replace("mapbox://styles/", "")

TILE_URL = (
    f"https://api.mapbox.com/styles/v1/{style_path}/tiles/256/{{z}}/{{x}}/{{y}}@2x"
    f"?access_token={MAPBOX_TOKEN}"
)

TILE_ATTRIBUTION = (
    '© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> '
    '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
)

print("=" * 60)
print("  Fort Worth Tacos — Custom TCU-Themed Mapbox Style Map")
print("=" * 60)
print(f"\nUsing custom style: {MAPBOX_STYLE_URL}")


# =============================================================================
# STEP 4: LOAD THE GEOCODED DATA
# =============================================================================
input_path = os.path.join("data", "fw_tacos_geocoded.csv")

if not os.path.exists(input_path):
    print(f"\nERROR: File not found: {input_path}")
    print("Please run Script 2 first: 02_geocode_map_basic.py")
    exit()

df = pd.read_csv(input_path)
df_mapped = df.dropna(subset=["Latitude", "Longitude"]).copy()

print(f"\nLoaded {len(df)} shops. {len(df_mapped)} have coordinates for mapping.")


# =============================================================================
# STEP 5: CREATE MAP WITH CUSTOM BASEMAP
# =============================================================================
print("\nBuilding map with custom Mapbox basemap...")

center_lat = df_mapped["Latitude"].mean() if len(df_mapped) > 0 else 32.7555
center_lon = df_mapped["Longitude"].mean() if len(df_mapped) > 0 else -97.3308

# --- Create the Map ---
# The key difference from Script 2: we pass our Mapbox tile URL as the basemap
fw_map = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12,
    tiles=TILE_URL,
    attr=TILE_ATTRIBUTION
)

# --- Title ---
title_html = """
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
     z-index: 1000; background-color: rgba(77,25,121,0.9); padding: 10px 20px;
     border: 2px solid white; border-radius: 8px; font-family: Georgia, serif;
     font-size: 16px; font-weight: bold; color: white; box-shadow: 2px 2px 6px rgba(0,0,0,0.5);">
    🌮 Best Tacos in Fort Worth
</div>
"""
fw_map.get_root().html.add_child(folium.Element(title_html))

# --- Neighborhood Color Mapping ---
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
    neighborhood = row.get("Neighborhood", "")
    marker_color = NEIGHBORHOOD_COLORS.get(neighborhood, NEIGHBORHOOD_COLORS["Default"])

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

    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=f"🌮 {row['Name']}",
        icon=folium.Icon(color=marker_color, icon="cutlery", prefix="fa")
    ).add_to(fw_map)

# --- Legend ---
legend_html = """
<div style="position: fixed; bottom: 30px; left: 20px; z-index: 1000;
     background-color: rgba(255,255,255,0.92); padding: 12px;
     border: 2px solid #4D1979; border-radius: 8px;
     font-family: Arial, sans-serif; font-size: 12px;">
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
# STEP 6: SAVE THE MAP
# =============================================================================
os.makedirs("data", exist_ok=True)
output_path = os.path.join("data", "fw_tacos_map_custom.html")
fw_map.save(output_path)

print(f"  Map saved to: {output_path}")
print("\n" + "=" * 60)
print("  SCRIPT COMPLETE!")
print("=" * 60)
print(f"\nCompare your two maps side by side:")
print(f"  data/fw_tacos_map_basic.html   ← plain OpenStreetMap")
print(f"  data/fw_tacos_map_custom.html  ← YOUR custom TCU-themed style")
print(f"\nThis file is ready to add to your portfolio!")
