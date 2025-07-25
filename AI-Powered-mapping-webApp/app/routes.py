from flask import Blueprint, request, jsonify, session, current_app, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
import geopandas as gpd
import pandas as pd
from flask_login import login_required, current_user
from app.utils.ai_handler import process_user_query
from app.utils.map_generator import generate_map_response
from app.utils.style_parser import parse_style_instructions
from app.utils.file_processor import process_uploaded_file
from app.utils.raster_processor import calculate_index, create_raster_visualization
import rasterio
import zipfile
import traceback

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/gis')
@login_required
def index():
    return render_template('gis/index.html')

@main_bp.route('/api/process-query', methods=['POST'])
@login_required
def process_query():
    data = request.get_json()
    user_message = data.get('message', '')
    
    try:
        if 'current_geojson' not in session or 'gdf_columns' not in session:
            return jsonify({
                'ai_response': 'Please upload a GeoJSON file first! 📁',
                'requires_file': True
            }), 400
                
        gdf = gpd.read_file(session['current_geojson'])
        columns = session.get('gdf_columns', [])
        
        ai_response, column_names = process_user_query(
            user_message, 
            columns,
            current_app.config['GENAI_API_KEY']
        )
        
        response_data = {'ai_response': ai_response}
        
        if column_names:
            if any(keyword in user_message.lower() for keyword in ['map', 'visualize', 'heatmap']):
                styles = parse_style_instructions(user_message)
                map_data = generate_map_response(gdf, column_names, styles, user_message)
                response_data.update(map_data)
            
            if any(keyword in user_message.lower() for keyword in ['statistics', 'stats', 'plot', 'chart']):
                stats = {}
                for col in column_names:
                    if pd.api.types.is_numeric_dtype(gdf[col]):
                        stats[col] = gdf[col].describe().to_dict()
                    else:
                        stats[col] = f"Statistics not available for non-numeric column: {col}"
                response_data['statistics'] = stats
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/upload-file', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        filename = secure_filename(file.filename)
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # Simple file type detection
        if filename.lower().endswith(('.geojson', '.json')):
            gdf = gpd.read_file(filepath)
            session['current_geojson'] = filepath
            session['gdf_columns'] = list(gdf.columns)
            return jsonify({
                'message': 'File uploaded successfully',
                'file_type': 'vector',
                'columns': list(gdf.columns)
            })
        elif filename.lower().endswith(('.tif', '.tiff')):
            return jsonify({
                'message': 'Raster file uploaded',
                'file_type': 'raster',
                'filepath': filepath
            })
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'File processing error: {str(e)}'}), 500
    
def calculate_raster_index():
    data = request.get_json()
    
    try:
        index_data = calculate_index(
            data['raster_path'],
            data['index_type'],
            data['bands']
        )
        
        image_data = create_raster_visualization(index_data, data['index_type'])
        
        return jsonify({
            'index_type': data['index_type'],
            'image_data': image_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400