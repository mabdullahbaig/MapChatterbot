def parse_style_instructions(message):
    """Parse user message for style instructions"""
    styles = {
        "legend_loc": "lower left",
        "legend_size": "medium",
        "north_arrow_position": "top right",
        "color_scheme": "YlGn",
        "grid": False,  # Default grid visibility
        "scale_bar": True,  # Default scale bar visibility
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
    elif "north arrow to bottom" in message.lower():
        styles["north_arrow_position"] = "bottom"

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

def add_north_arrow(ax, position='top right'):
    """Add a north arrow to the map."""
    if position == 'top right':
        x, y, dx, dy = 0.95, 0.95, 0.05, 0.05
    elif position == 'top left':
        x, y, dx, dy = 0.05, 0.95, 0.05, 0.05
    elif position == 'bottom':
        x, y, dx, dy = 0.5, 0.05, 0.05, 0.05
    else:
        x, y, dx, dy = 0.95, 0.95, 0.05, 0.05  # Default to top right

    ax.annotate(
        'N', xy=(x, y), xytext=(x - dx, y - dy),
        arrowprops=dict(facecolor='black', shrink=0.05),
        ha='center', va='center', fontsize=12, xycoords='axes fraction'
    )