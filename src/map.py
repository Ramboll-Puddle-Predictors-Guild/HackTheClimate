import geopandas as gpd



def generate_map(windfarm):
    # Load the GeoJSON files
    gdf_denmark = gpd.read_file("location\denmark.json")  # Denmark data
    gdf_latvia = gpd.read_file("location\latvia.json")  # Latvia data
    
    # Filter the GeoDataFrames
    nordsren_iii_vest = gdf_denmark[gdf_denmark["name"] == "Nordsren III vest"]
    latvia_wind_farm = gdf_latvia  

    # Calculate average coordinates for Denmark and Latvia individually
    lat_denmark, lon_denmark = calculate_average_coords(nordsren_iii_vest)
    lat_latvia, lon_latvia = calculate_average_coords(latvia_wind_farm)

    # Create focused maps based on user selection
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