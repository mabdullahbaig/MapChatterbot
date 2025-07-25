import os
import zipfile
import tempfile
import geopandas as gpd
import rasterio
from werkzeug.utils import secure_filename
from flask import current_app

def get_file_type(filename):
    """Determine file type based on extension"""
    ext = filename.split('.')[-1].lower()
    
    if ext in ['geojson', 'json']:
        return 'geojson'
    elif ext in ['shp', 'shx', 'dbf', 'prj']:
        return 'shapefile'
    elif ext in ['tif', 'tiff']:
        return 'raster'
    elif ext == 'zip':
        return 'shapefile'  # Assuming zip contains shapefile
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def process_uploaded_file(file):
    try:
        filename = secure_filename(file.filename)
        file_type = get_file_type(filename)
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        if file_type == 'shapefile':
            # Handle shapefile (zipped or individual files)
            temp_dir = tempfile.mkdtemp()
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            
            # If it's a zip file, extract it
            if filename.endswith('.zip'):
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                # Find the .shp file
                shp_file = None
                for f in os.listdir(temp_dir):
                    if f.endswith('.shp'):
                        shp_file = os.path.join(temp_dir, f)
                        break
                if not shp_file:
                    raise ValueError("No .shp file found in the uploaded zip")
                gdf = gpd.read_file(shp_file)
            else:
                # Handle individual shapefile component
                gdf = gpd.read_file(filepath)
            
            # Save as GeoJSON for consistency
            output_path = os.path.join(upload_dir, os.path.splitext(filename)[0] + '.geojson')
            gdf.to_file(output_path, driver='GeoJSON')
            return {
                'message': 'Shapefile uploaded and converted to GeoJSON',
                'filepath': output_path,
                'columns': list(gdf.columns),
                'file_type': 'vector'
            }
            
        elif file_type == 'raster':
            # Handle raster files
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            with rasterio.open(filepath) as src:
                return {
                    'message': 'Raster file uploaded successfully',
                    'filepath': filepath,
                    'file_type': 'raster',
                    'band_count': src.count
                }
                
        else:  # GeoJSON
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            gdf = gpd.read_file(filepath)
            return {
                'message': 'GeoJSON file uploaded successfully',
                'filepath': filepath,
                'columns': list(gdf.columns),
                'file_type': 'vector'
            }
            
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")

# ALLOWED_EXTENSIONS = {
#     'geojson': ['.geojson', '.json'],
#     'shapefile': ['.shp', '.shx', '.dbf', '.prj'],
#     'raster': ['.tif', '.tiff']
# }

# def allowed_file(filename, file_type):
#     ext = os.path.splitext(filename)[1].lower()
#     return ext in ALLOWED_EXTENSIONS.get(file_type, [])

# def process_uploaded_file(file, file_type):
#     try:
#         filename = secure_filename(file.filename)
#         upload_dir = current_app.config['UPLOAD_FOLDER']
#         os.makedirs(upload_dir, exist_ok=True)
        
#         if file_type == 'shapefile':
#             temp_dir = tempfile.mkdtemp()
#             zip_path = os.path.join(temp_dir, filename)
#             file.save(zip_path)
            
#             with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#                 zip_ref.extractall(temp_dir)
            
#             shp_file = None
#             for f in os.listdir(temp_dir):
#                 if f.endswith('.shp'):
#                     shp_file = os.path.join(temp_dir, f)
#                     break
            
#             if not shp_file:
#                 raise ValueError("No .shp file found in the uploaded zip")
            
#             gdf = gpd.read_file(shp_file)
#             filepath = os.path.join(upload_dir, os.path.splitext(filename)[0] + '.geojson')
#             gdf.to_file(filepath, driver='GeoJSON')
            
#         elif file_type == 'raster':
#             filepath = os.path.join(upload_dir, filename)
#             file.save(filepath)
            
#             with rasterio.open(filepath) as src:
#                 pass  # Validate raster
                
#             return {
#                 'message': 'Raster file uploaded successfully',
#                 'filepath': filepath,
#                 'file_type': 'raster',
#                 'band_count': src.count
#             }
            
#         else:  # GeoJSON
#             filepath = os.path.join(upload_dir, filename)
#             file.save(filepath)
#             gdf = gpd.read_file(filepath)
            
#         return {
#             'message': 'File uploaded successfully',
#             'filepath': filepath,
#             'columns': list(gdf.columns),
#             'file_type': 'vector'
#         }
        
#     except Exception as e:
#         raise ValueError(f"Error processing {file_type}: {str(e)}")