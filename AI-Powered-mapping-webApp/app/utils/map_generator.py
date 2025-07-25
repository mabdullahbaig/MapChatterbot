import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd
import pandas as pd
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import folium
from folium.plugins import HeatMap, Draw, Fullscreen, MeasureControl
import mapclassify
import branca.colormap as cm
import numpy as np
from folium.plugins import HeatMap

def generate_map_response(gdf, columns, styles, user_message):
    """Main function to generate appropriate map response based on user request"""
    response = {}

    # Clean data by filling NaN values
    for col in columns:
        if gdf[col].dtype in ['float64', 'int64']:
            gdf[col] = gdf[col].fillna(0)

    if "heatmap" in user_message.lower() or "density" in user_message.lower():
        response['map_html'] = create_heatmap(gdf, columns[0])
    elif "interactive" in user_message.lower() or "dynamic" in user_message.lower():
        response['map_html'] = create_interactive_map(gdf, columns[0], user_message)
    else:
        response['map_image'] = create_static_map(gdf, columns[0], styles, user_message)

    return response

def create_heatmap(gdf, column):
    """Generate a heatmap with error handling and null checks"""
    try:
        # Validate input
        if gdf.empty or column not in gdf.columns:
            raise ValueError("⚠️ Invalid data or column name")
       
        # Filter valid geometries and values
        valid_data = []
        for i, row in gdf.iterrows():
            if (not pd.isna(row[column]) and
                    row.geometry is not None and
                    not row.geometry.is_empty):
                try:
                    centroid = row.geometry.centroid
                    valid_data.append([
                        centroid.y,
                        centroid.x,
                        float(row[column])  # Ensure numeric value
                    ])
                except (AttributeError, ValueError):
                    continue
       
        if not valid_data:
            raise ValueError("🔴 No valid data points for heatmap")
       
        # Create map centered on data
        avg_lat = sum(p[0] for p in valid_data)/len(valid_data)
        avg_lon = sum(p[1] for p in valid_data)/len(valid_data)
       
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=10 if len(valid_data) > 100 else 12,
            control_scale=True
        )

        # Add heatmap with named layer
        heat_layer = HeatMap(
            valid_data,
            radius=20 if len(valid_data) > 500 else 15,
            blur=15,
            max_zoom=15,
            min_opacity=0.5,
            gradient={0.4: 'blue', 0.6: 'lime', 0.8: 'orange', 1: 'red'},
            name="DensityHeatmap"  # Unique layer identifier
        ).add_to(m)

        # Add interactive controls
        _add_heatmap_controls(m)
        return m._repr_html_()

    except Exception as e:
        error_html = f"""
        <div style="color:red; padding:20px; font-family:sans-serif">
            <h3>⚠️ Heatmap Error</h3>
            <p>{str(e)}</p>
            <p>💡 Try: 'check data quality' or 'use different column'</p>
        </div>
        """
        return error_html

def _add_heatmap_controls(map_obj):
    """Add interactive controls to heatmap"""
    controls = """
    <div id="heatmapControls" style="position:fixed; bottom:20px; left:20px; z-index:1000; background:white; padding:10px; border-radius:5px; box-shadow:0 0 10px rgba(0,0,0,0.3); width:300px;">
        <h4 style="margin-top:0;">🔥 Heatmap Controls</h4>
       
        <div class="control-group">
            <label>Opacity: <span id="heatOpacityValue">0.7</span></label>
            <input type="range" id="heatOpacitySlider" min="0" max="1" step="0.05" value="0.7" style="width:100%">
        </div>
       
        <div class="control-group">
            <label>Intensity: <span id="heatRadiusValue">15</span></label>
            <input type="range" id="heatRadiusSlider" min="5" max="30" step="1" value="15" style="width:100%">
        </div>
    </div>

    <script>
        // Opacity control
        document.getElementById('heatOpacitySlider').addEventListener('input', function(e) {
            document.getElementById('heatOpacityValue').textContent = e.target.value;
            map.eachLayer(function(layer) {
                if (layer.options && layer.options.name === 'DensityHeatmap') {
                    layer.setOptions({minOpacity: parseFloat(e.target.value)});
                }
            });
        });

        // Radius control
        document.getElementById('heatRadiusSlider').addEventListener('input', function(e) {
            document.getElementById('heatRadiusValue').textContent = e.target.value;
            map.eachLayer(function(layer) {
                if (layer.options && layer.options.name === 'DensityHeatmap') {
                    layer.setOptions({radius: parseInt(e.target.value)});
                }
            });
        });
    </script>
    """
    map_obj.get_root().html.add_child(folium.Element(controls))

def create_static_map(gdf, column, styles, user_message):
    # Default styles if not provided
    default_styles = {
        'legend_loc': 'lower right',
        'legend_size': 'small',
        'legend_size': 'small',  # To also reduce font size
        'legend_markerscale': 0.5,
        'legend_handlelength': 1.0,
        'legend_labelspacing': 0.6,
        'legend_handletextpad': 0.3,
        'title_fontsize': 14,
        'legend_title_fontsize': 8,
        'color_scheme': 'YlGn',
        'classification_scheme': 'NaturalBreaks',
        'k_classes': 5,
        'north_arrow_position': 'top right',
        'grid': False,
        'scale_bar': True,
        'padding': 0.1,
        'title': f"{column} Distribution",
        'legend_title': column
    }

    # Extract title from user message if specified
    if "title" in user_message.lower():
        title_part = user_message.split("title")[1].strip()
        if len(title_part) > 0:
            default_styles['title'] = title_part.split(".")[0].strip()

    # Extract legend title from user message if specified
    if "legend title" in user_message.lower():
        legend_part = user_message.split("legend title")[1].strip()
        if len(legend_part) > 0:
            default_styles['legend_title'] = legend_part.split(".")[0].strip()

    # Merge user styles with defaults
    styles = {**default_styles, **styles}

    # Calculate the geographic extent of the data
    xmin, ymin, xmax, ymax = gdf.total_bounds
    width = xmax - xmin
    height = ymax - ymin

    # Adjust figure size dynamically based on the extent
    aspect_ratio = width / height
    if aspect_ratio > 1:  # Wider than tall
        fig_width = 10
        fig_height = 10 / aspect_ratio
    else:  # Taller than wide
        fig_height = 10
        fig_width = 10 * aspect_ratio

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    try:
        # Handle categorical/non-numeric data
        if gdf[column].dtype == 'object' or not pd.api.types.is_numeric_dtype(gdf[column]):
            unique_values = gdf[column].unique()
            num_categories = len(unique_values)

            # Use a colormap with enough distinct colors
            cmap = plt.get_cmap('tab20', num_categories) if num_categories > 10 else plt.get_cmap('tab10', num_categories)

            # Create a dictionary mapping categories to colors
            color_dict = {val: cmap(i) for i, val in enumerate(unique_values)}

            # Plot each category with its assigned color
            for val, color in color_dict.items():
                gdf[gdf[column] == val].plot(ax=ax, color=color, label=str(val))

            # Create legend
            legend_elements = [
                Patch(facecolor=color_dict[val], edgecolor='black', label=str(val))
                for val in unique_values
            ]

            ax.legend(
                handles=legend_elements,
                title=styles['legend_title'],
                loc=styles['legend_loc'],
                fontsize=styles['legend_size'],
                title_fontsize=styles['legend_title_fontsize'],
                frameon=True,
                framealpha=0.8
            )

        else:  # Numeric data
            # Ensure numeric type and handle NaN values
            gdf[column] = pd.to_numeric(gdf[column], errors='coerce').fillna(0)

            # Apply classification
            if styles["classification_scheme"] == "NaturalBreaks":
                classifier = mapclassify.NaturalBreaks(gdf[column], k=styles["k_classes"])
            elif styles["classification_scheme"] == "EqualInterval":
                classifier = mapclassify.EqualInterval(gdf[column], k=styles["k_classes"])
            elif styles["classification_scheme"] == "Quantiles":
                classifier = mapclassify.Quantiles(gdf[column], k=styles["k_classes"])
            else:
                classifier = mapclassify.NaturalBreaks(gdf[column], k=styles["k_classes"])

            # Plot with classified values
            plot = gdf.plot(
                column=column,
                cmap=styles["color_scheme"],
                scheme=styles["classification_scheme"].lower(),
                classification_kwds={"k": styles["k_classes"]},
                legend=True,
                legend_kwds={
                    "loc": styles["legend_loc"],
                    "title": styles['legend_title'],
                    "fmt": "{:.0f}",
                    "fontsize": styles['legend_size'],
                    "title_fontsize": styles['legend_title_fontsize'],
                    "frameon": True,
                    "framealpha": 0.8
                },
                ax=ax
            )

            # Customize legend labels
            legend = ax.get_legend()
            if legend:
                class_bins = classifier.bins
                labels = []
                for i in range(len(class_bins)):
                    if i == 0:
                        labels.append(f"< {class_bins[i]:.2f}")
                    else:
                        labels.append(f"{class_bins[i-1]:.2f} - {class_bins[i]:.2f}")

                # Update legend labels
                for text, new_label in zip(legend.get_texts(), labels):
                    text.set_text(new_label)

                # Replace circular markers with rectangular patches
                for handle in legend.legend_handles:
                    handle.set_marker("s")

        # Set title
        ax.set_title(styles['title'], fontsize=styles['title_fontsize'], pad=20)

        # Set geographic extent with padding
        padding = styles['padding']
        ax.set_xlim(xmin - padding * width, xmax + padding * width)
        ax.set_ylim(ymin - padding * height, ymax + padding * height)

        # Add north arrow
        _add_north_arrow(ax, position=styles['north_arrow_position'])

        # Add grid if enabled
        if styles['grid']:
            ax.grid(True, linestyle='--', alpha=0.5)

        if styles.get('scale_bar', False):
            # Assuming the CRS is in degrees (EPSG:4326) for a rough estimate
            # The length of a degree of longitude varies with latitude, so this is an approximation.
            # A more accurate method would involve projecting the data to a metric CRS.

            # Approximate center latitude for scale calculation
            center_lat = (ymin + ymax) / 2

            # Approximate length of 1 degree of longitude at the center latitude (in km)
            lon_degree_km = 111.320 * np.cos(np.deg2rad(center_lat))
            lat_degree_km = 110.574

            # Determine a reasonable scale bar length in km (e.g., 5 km)
            target_length_km = 5

            # Calculate the corresponding length in degree units (using longitude for width)
            scale_bar_length_degrees = target_length_km / lon_degree_km if lon_degree_km > 0 else 0.05 * width # Fallback

            # Position the scale bar at the bottom center
            scale_bar_position_x = xmin + width / 2 - scale_bar_length_degrees / 2
            scale_bar_position_y = ymin + height * 0.01  # Slightly above the bottom

            ax.plot([scale_bar_position_x, scale_bar_position_x + scale_bar_length_degrees],
                    [scale_bar_position_y, scale_bar_position_y],
                    color='black', linewidth=3)

            ax.text(scale_bar_position_x + scale_bar_length_degrees / 2, scale_bar_position_y - height * 0.02,
                    f"{target_length_km} km", ha='center', va='top', fontsize=10)

            ax.text(scale_bar_position_x, scale_bar_position_y - height * 0.04,
                    "0", ha='right', va='top', fontsize=8)
            ax.text(scale_bar_position_x + scale_bar_length_degrees, scale_bar_position_y - height * 0.04,
                    f"{target_length_km}", ha='left', va='top', fontsize=8)


        # Save to buffer
        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        img.seek(0)

        return f"data:image/png;base64,{base64.b64encode(img.read()).decode('utf-8')}"

    except Exception as e:
        plt.close(fig)
        raise ValueError(f"Error generating static map: {str(e)}")

def create_interactive_map(gdf, column, user_message):
    """
    Creates an interactive map with a choropleth layer and integrated layer controls.
    Handles both numeric and categorical data with appropriate visualization.

    Args:
        gdf (gpd.GeoDataFrame): The GeoDataFrame containing the geographic data and the column to visualize.
        column (str): The name of the column in the GeoDataFrame to use for the choropleth.
        user_message (str): The user's message, which can contain instructions for the map (e.g., title).

    Returns:
        str: An HTML representation of the interactive Folium map.

    Raises:
        ValueError: If there is an error during map creation.
    """
    try:
        # Handle NaN values
        if gdf[column].isna().any():
            if gdf[column].dtype in ['float64', 'int64']:
                gdf[column] = gdf[column].fillna(0)
            else:
                gdf[column] = gdf[column].fillna('Unknown')

        # Reproject to Web Mercator for accurate display
        gdf_projected = gdf.to_crs(epsg=3857)
        centroid = gdf_projected.geometry.centroid
        center_wgs84 = gpd.GeoSeries([gpd.points_from_xy([centroid.x.mean()], [centroid.y.mean()])[0]], 
                                    crs="EPSG:3857").to_crs(epsg=4326)
        center = [center_wgs84.y.iloc[0], center_wgs84.x.iloc[0]]

        # Create base map
        m = folium.Map(location=center, zoom_start=6, tiles=None)
        
        # Add multiple basemap options
        folium.TileLayer(
            "OpenStreetMap",
            name="OpenStreetMap",
            attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
        ).add_to(m)
        folium.TileLayer(
            "Stamen Terrain",
            name="Stamen Terrain",
            attr="Map tiles by <a href='http://stamen.com'>Stamen Design</a>, under <a href='http://creativecommons.org/licenses/by/3.0'>CC BY 3.0</a>. Data by <a href='http://openstreetmap.org'>OpenStreetMap</a>, under <a href='http://www.openstreetmap.org/copyright'>ODbL</a>."
        ).add_to(m)
        folium.TileLayer(
            "Stamen Toner",
            name="Stamen Toner",
            attr="Map tiles by <a href='http://stamen.com'>Stamen Design</a>, under <a href='http://creativecommons.org/licenses/by/3.0'>CC BY 3.0</a>. Data by <a href='http://openstreetmap.org'>OpenStreetMap</a>, under <a href='http://www.openstreetmap.org/copyright'>ODbL</a>."
        ).add_to(m)
        folium.TileLayer(
            "Stamen Watercolor",
            name="Stamen Watercolor",
            attr="Map tiles by <a href='http://stamen.com'>Stamen Design</a>, under <a href='http://creativecommons.org/licenses/by/3.0'>CC BY 3.0</a>. Data by <a href='http://openstreetmap.org'>OpenStreetMap</a>, under <a href='http://www.openstreetmap.org/copyright'>ODbL</a>."
        ).add_to(m)
        folium.TileLayer(
            "CartoDB positron",
            name="CartoDB Positron",
            attr='&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'
        ).add_to(m)
        folium.TileLayer(
            "CartoDB dark_matter",
            name="CartoDB Dark Matter",
            attr='&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'
        ).add_to(m)

        # Determine if data is categorical or numeric
        is_categorical = gdf[column].dtype == 'object' or not pd.api.types.is_numeric_dtype(gdf[column])
        
        if is_categorical:
            # Categorical data visualization
            unique_values = gdf[column].unique()
            color_map = cm.linear.Set3_12.scale(0, len(unique_values)-1)
            
            def style_function(feature):
                val = feature['properties'][column]
                try:
                    idx = list(unique_values).index(val)
                    return {'fillColor': color_map(idx), 'color': 'black', 'weight': 0.5}
                except:
                    return {'fillColor': 'gray', 'color': 'black', 'weight': 0.5}
            
            # Add GeoJson layer
            geojson_layer = folium.GeoJson(
                gdf,
                style_function=style_function,
                tooltip=folium.GeoJsonTooltip(fields=[column], aliases=[column+":"]),
                name=column
            ).add_to(m)
            
            # Add legend for categorical data
            legend_html = f"""
            <div style="position: fixed;
                     bottom: 50px; right: 50px;
                     width: 150px; height: auto;
                     background-color: white;
                     border:2px solid grey; z-index:9999;
                     padding: 10px;
                     font-size:12px;
                     overflow-y: auto;
                     max-height: 300px;">
             <p style="margin:0;font-weight:bold;">{column}</p>
             {''.join([f'<div><i style="background:{color_map(i)};width:15px;height:15px;display:inline-block;"></i> {val}</div>'
                       for i, val in enumerate(unique_values)])}
        </div>
        """
            m.get_root().html.add_child(folium.Element(legend_html))
            
        else:
            # Numeric data visualization
            # Create choropleth with color scale
            if gdf[column].nunique() > 1:
                # Use 'GEOID' or 'STUSPS' as the key if available, otherwise use index
                key_column = 'GEOID' if 'GEOID' in gdf.columns else 'STUSPS' if 'STUSPS' in gdf.columns else gdf.index.name
                
                choropleth = folium.Choropleth(
                    geo_data=gdf,
                    name="Choropleth",
                    data=gdf,
                    columns=[key_column, column],
                    key_on=f"feature.properties.{key_column}" if key_column in gdf.columns else "feature.id",
                    fill_color="YlGn",
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    legend_name=column,
                    bins=7,
                    highlight=True
                ).add_to(m)
                
                # Add tooltip
                folium.features.GeoJsonTooltip(
                    fields=[key_column, column] if key_column in gdf.columns else [column],
                    aliases=["State ID: ", f"{column}: "] if key_column in gdf.columns else [f"{column}: "],
                    labels=True,
                    sticky=True
                ).add_to(choropleth.geojson)
            else:
                # Handle case where all values are the same
                geojson_layer = folium.GeoJson(
                    gdf,
                    style_function=lambda x: {
                        'fillColor': '#1f77b4',
                        'color': 'black',
                        'weight': 0.5
                    },
                    tooltip=folium.GeoJsonTooltip(fields=[column], aliases=[column+":"]),
                    name=column
                ).add_to(m)
        
        # Add layer control
                
        # Add map controls (no JavaScript needed as it's in main.js)
        Fullscreen().add_to(m)
        MeasureControl().add_to(m)
        # Add additional tools
        folium.LayerControl(position="topleft").add_to(m)  # Keep layer control in top right
        MeasureControl(primary_length_unit='kilometers', position="bottomleft").add_to(m)  # Move MeasureControl to bottom left
        Draw(position="bottomright").add_to(m)
        
        # Add title if specified in user message
        if "title" in user_message.lower():
            title_part = user_message.split("title")[1].strip()
            if len(title_part) > 0:
                title = title_part.split(".")[0].strip()
                title_html = f'''
                <h3 style="position: fixed; 
                           top: 10px; left: 50%; 
                           transform: translateX(-50%);
                           background-color: white; 
                           padding: 5px 15px;
                           border-radius: 5px;
                           border: 1px solid grey;
                           z-index: 9999;
                           font-family: Arial, sans-serif;">
                    {title}
                </h3>
                '''
                m.get_root().html.add_child(folium.Element(title_html))
        
        return m._repr_html_()
    
    except Exception as e:
        raise ValueError(f"Error creating interactive map: {str(e)}")

def _add_north_arrow(ax, position='top right'):
    """Add a professional-looking north arrow to matplotlib plot"""
    arrow_style = dict(
        facecolor='black',
        edgecolor='black',
        arrowstyle='->,head_width=0.4,head_length=0.6',
        linewidth=1,
        shrinkA=0,
        shrinkB=0
    )

    if position == 'top right':
        x, y = 0.95, 0.95
        xytext = (x, y-0.05)
    elif position == 'top left':
        x, y = 0.05, 0.95
        xytext = (x, y-0.05)
    elif position == 'bottom right':
        x, y = 0.95, 0.05
        xytext = (x, y+0.05)
    elif position == 'bottom left':
        x, y = 0.05, 0.05
        xytext = (x, y+0.05)
    else:  # default to top right
        x, y = 0.95, 0.95
        xytext = (x, y-0.05)

    ax.annotate(
        'N',
        xy=(x, y),
        xytext=xytext,
        arrowprops=arrow_style,
        ha='center',
        va='center',
        fontsize=12,
        xycoords='axes fraction',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', alpha=0.8)
    )

def parse_style_instructions(message):
    """Parse user message for style instructions"""
    styles = {
        "legend_loc": "lower left",
        'legend_size': 'small',  # To also reduce font size
        'legend_markerscale': 0.5,
        'legend_handlelength': 1.0,
        'legend_labelspacing': 0.6,
        'legend_handletextpad': 0.3,
        "north_arrow_position": "top right",
        "color_scheme": "YlGn",
        "grid": False,
        "scale_bar": True,
    }

    # Legend position parsing
    if "legend to left" in message.lower():
        styles["legend_loc"] = "upper left"
    elif "legend to right" in message.lower():
        styles["legend_loc"] = "upper right"
    elif "legend to bottom left" in message.lower():
        styles["legend_loc"] = "lower left"
    elif "legend to bottom right" in message.lower():
        styles["legend_loc"] = "lower right"

    # Legend size parsing
    if "legend size small" in message.lower():
        styles["legend_size"] = "small"
    elif "legend size large" in message.lower():
        styles["legend_size"] = "large"

    # North arrow position parsing
    if "north arrow to top left" in message.lower():
        styles["north_arrow_position"] = "top left"
    elif "north arrow to bottom right" in message.lower():
        styles["north_arrow_position"] = "bottom right"
    elif "north arrow to bottom left" in message.lower():
        styles["north_arrow_position"] = "bottom left"
    elif "north arrow to top right" in message.lower():
        styles["north_arrow_position"] = "top right"

    # Color scheme parsing
    color_mapping = {
        "blues": "Blues",
        "reds": "Reds",
        "greens": "Greens",
        "purples": "Purples",
        "ylgn": "YlGn",
    }
    for key, value in color_mapping.items():
        if f"color scheme {key}" in message.lower():
            styles["color_scheme"] = value
            break

    # Grid and scale bar parsing
    if "show grid" in message.lower():
        styles["grid"] = True
    if "hide scale bar" in message.lower():
        styles["scale_bar"] = False

    return styles