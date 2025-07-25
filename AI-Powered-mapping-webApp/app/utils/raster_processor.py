import rasterio
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def calculate_index(raster_path, index_type, bands):
    with rasterio.open(raster_path) as src:
        band_data = {band: src.read(band) for band in bands}
        
        if index_type == 'NDVI':
            nir, red = band_data[bands[0]], band_data[bands[1]]
            ndvi = (nir.astype(float) - red.astype(float)) / (nir + red + 1e-10)
            return ndvi
            
        elif index_type == 'NDWI':
            green, nir = band_data[bands[0]], band_data[bands[1]]
            ndwi = (green.astype(float) - nir.astype(float)) / (green + nir + 1e-10)
            return ndwi
            
        elif index_type == 'SAWI':
            nir, swir = band_data[bands[0]], band_data[bands[1]]
            sawi = (nir.astype(float) - swir.astype(float)) / (nir + swir + 1e-10)
            return sawi

def create_raster_visualization(index_data, index_type):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    if index_type == 'NDVI':
        cmap = 'YlGn'
        vmin, vmax = -1, 1
    elif index_type == 'NDWI':
        cmap = 'Blues'
        vmin, vmax = -1, 1
    else:  # SAWI
        cmap = 'RdYlBu'
        vmin, vmax = -1, 1
    
    img = ax.imshow(index_data, cmap=cmap, vmin=vmin, vmax=vmax)
    plt.colorbar(img, ax=ax, label=index_type)
    ax.set_title(f'{index_type} Visualization')
    ax.axis('off')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close()
    buf.seek(0)
    
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"

# import rasterio
# import numpy as np
# from rasterio.plot import reshape_as_image
# import matplotlib.pyplot as plt
# from io import BytesIO
# import base64

# def calculate_index(raster_path, index_type, bands):
#     with rasterio.open(raster_path) as src:
#         band_data = {band: src.read(band) for band in bands}
        
#         if index_type == 'NDVI':
#             # NDVI = (NIR - Red) / (NIR + Red)
#             nir, red = band_data[bands[0]], band_data[bands[1]]
#             ndvi = (nir.astype(float) - red.astype(float)) / (nir + red)
#             return ndvi
            
#         elif index_type == 'NDWI':
#             # NDWI = (Green - NIR) / (Green + NIR)
#             green, nir = band_data[bands[0]], band_data[bands[1]]
#             ndwi = (green.astype(float) - nir.astype(float)) / (green + nir)
#             return ndwi
            
#         elif index_type == 'SAWI':
#             # SAWI = (NIR - SWIR) / (NIR + SWIR)
#             nir, swir = band_data[bands[0]], band_data[bands[1]]
#             sawi = (nir.astype(float) - swir.astype(float)) / (nir + swir)
#             return sawi

# def create_raster_visualization(index_data, index_type):
#     fig, ax = plt.subplots(figsize=(10, 10))
    
#     # Create color map based on index type
#     if index_type == 'NDVI':
#         cmap = 'YlGn'
#         vmin, vmax = -1, 1
#     elif index_type == 'NDWI':
#         cmap = 'Blues'
#         vmin, vmax = -1, 1
#     else:  # SAWI
#         cmap = 'RdYlBu'
#         vmin, vmax = -1, 1
    
#     img = ax.imshow(index_data, cmap=cmap, vmin=vmin, vmax=vmax)
#     plt.colorbar(img, ax=ax, label=index_type)
#     ax.set_title(f'{index_type} Visualization')
#     ax.axis('off')
    
#     # Save to buffer
#     buf = BytesIO()
#     plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
#     plt.close()
#     buf.seek(0)
    
#     return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"