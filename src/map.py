from pathlib import Path

import folium
import geopandas as gpd
import numpy as np

LOCATION_DATA = Path(__file__).parent.parent / "location"


def generate_map(windfarm):
    # Load the GeoJSON files
    gdf_denmark = gpd.read_file(LOCATION_DATA / "denmark.json")  # Denmark data
    gdf_latvia = gpd.read_file(LOCATION_DATA / "latvia.json")  # Latvia data

    # Filter the GeoDataFrames
    nordsren_iii_vest = gdf_denmark[gdf_denmark["name"] == "Nordsren III vest"]
    latvia_wind_farm = gdf_latvia

    # Function to calculate the average coordinates from a GeoDataFrame
    def calculate_average_coords(gdf: gpd.GeoDataFrame):
        lats, lons = [], []
        for geom in gdf.geometry:
            if geom.geom_type == "MultiPolygon":
                for polygon in geom.geoms:
                    xs, ys = polygon.exterior.xy
                    lats.extend(ys)
                    lons.extend(xs)
            elif geom.geom_type == "Polygon":
                xs, ys = geom.exterior.xy
                lats.extend(ys)
                lons.extend(xs)
        return np.mean(lats), np.mean(lons)

    # Function to extract coordinates for plotting
    def extract_coords(gdf):
        coords = []
        for geom in gdf.geometry:
            if geom.geom_type == "MultiPolygon":
                for polygon in geom.geoms:
                    exterior_coords = [
                        [point[1], point[0]] for point in polygon.exterior.coords
                    ]
                    coords.append(exterior_coords)
            elif geom.geom_type == "Polygon":
                exterior_coords = [
                    [point[1], point[0]] for point in geom.exterior.coords
                ]
                coords.append(exterior_coords)
        return coords

    # Calculate average coordinates for Denmark and Latvia individually
    lat_denmark, lon_denmark = calculate_average_coords(nordsren_iii_vest)
    lat_latvia, lon_latvia = calculate_average_coords(latvia_wind_farm)

    # Create focused maps based on user selection
    print(windfarm)
    focused_map = folium.Map(
        location=(
            [lat_denmark, lon_denmark]
            if windfarm == "nordsen iii vest"
            else [lat_latvia, lon_latvia]
        ),
        zoom_start=7,
    )

    # Add polygons based on user selection
    if windfarm == "nordsen iii vest":
        denmark_coords = extract_coords(nordsren_iii_vest)
        for polygon in denmark_coords:
            folium.Polygon(
                locations=polygon,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.5,
            ).add_to(focused_map)

    elif windfarm == "e2":
        latvia_coords = extract_coords(latvia_wind_farm)
        for polygon in latvia_coords:
            folium.Polygon(
                locations=polygon,
                color="green",
                fill=True,
                fill_color="green",
                fill_opacity=0.5,
            ).add_to(focused_map)

    # Return the map
    return focused_map
