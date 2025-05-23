import os
import uuid
import base64 # Added base64
from io import BytesIO # Added BytesIO
from flask import Flask, request, send_file, jsonify, render_template
import cv2 
from image_processing.floor_replacement import replace_floor

app = Flask(__name__)
UPLOAD_FOLDER = 'temp_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the UPLOAD_FOLDER exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/replace_floor', methods=['POST'])
def handle_replace_floor():
    if 'room_image' not in request.files or 'tile_image' not in request.files:
        return jsonify({"error": "Both 'room_image' and 'tile_image' must be provided"}), 400

    room_file = request.files['room_image']
    tile_file = request.files['tile_image']

    if room_file.filename == '' or tile_file.filename == '':
        return jsonify({"error": "Filenames cannot be empty"}), 400

    # Generate unique filenames to avoid conflicts and save files
    room_filename = str(uuid.uuid4()) + os.path.splitext(room_file.filename)[1]
    tile_filename = str(uuid.uuid4()) + os.path.splitext(tile_file.filename)[1]
    
    room_image_path = os.path.join(app.config['UPLOAD_FOLDER'], room_filename)
    tile_image_path = os.path.join(app.config['UPLOAD_FOLDER'], tile_filename)
    
    output_filename = str(uuid.uuid4()) + ".jpg" # Output will be JPEG
    output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

    try:
        room_file.save(room_image_path)
        tile_file.save(tile_image_path)

        # Call the image processing function
        processed_image_array = replace_floor(room_image_path, tile_image_path)

        if processed_image_array is None:
            return jsonify({"error": "Image processing failed. Check server logs."}), 500

        # Save the resulting image
        success = cv2.imwrite(output_image_path, processed_image_array)
        if not success:
            return jsonify({"error": "Failed to save processed image."}), 500
        
        return send_file(output_image_path, mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        # Log the exception e for debugging
        print(f"An error occurred: {e}") # Basic logging
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        # Cleanup: Attempt to remove the files if they exist
        if os.path.exists(room_image_path):
            os.remove(room_image_path)
        if os.path.exists(tile_image_path):
            os.remove(tile_image_path)
        if os.path.exists(output_image_path):
            os.remove(output_image_path)

if __name__ == '__main__':
    # Note: For development, debug=True is fine. 
    # For production, use a proper WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, host='0.0.0.0', port=5000)


@app.route('/replace_floor_html', methods=['POST'])
def handle_replace_floor_html():
    if 'room_image' not in request.files or 'tile_image' not in request.files:
        return render_template('index.html', error_message='Missing room_image or tile_image')

    room_file = request.files['room_image']
    tile_file = request.files['tile_image']

    if room_file.filename == '' or tile_file.filename == '':
        return render_template('index.html', error_message='Filenames cannot be empty')

    # Generate unique filenames for temporary storage
    room_filename = str(uuid.uuid4()) + os.path.splitext(room_file.filename)[1]
    tile_filename = str(uuid.uuid4()) + os.path.splitext(tile_file.filename)[1]
    
    room_image_path = os.path.join(app.config['UPLOAD_FOLDER'], room_filename)
    tile_image_path = os.path.join(app.config['UPLOAD_FOLDER'], tile_filename)

    processed_image_array = None # Initialize

    try:
        # Save uploaded files
        room_file.save(room_image_path)
        tile_file.save(tile_image_path)

        # Call the image processing function
        # This is the core processing step.
        processed_image_array = replace_floor(room_image_path, tile_image_path)

        if processed_image_array is None:
            # This case handles failures within replace_floor that return None (e.g., image read issues)
            return render_template('index.html', error_message='Image processing failed. Check image validity or server logs.')

        # Encode result to base64 for embedding in HTML
        _, buffer = cv2.imencode('.jpg', processed_image_array)
        result_image_data = base64.b64encode(buffer).decode('utf-8')
        
        return render_template('index.html', result_image_data=result_image_data)

    except Exception as e:
        # Catch any other exceptions during file saving or processing
        print(f"Error in /replace_floor_html: {e}") # Log error
        return render_template('index.html', error_message='An unexpected error occurred during processing.')
    finally:
        # Cleanup: Attempt to remove the temporarily saved input files
        if os.path.exists(room_image_path):
            os.remove(room_image_path)
        if os.path.exists(tile_image_path):
            os.remove(tile_image_path)
