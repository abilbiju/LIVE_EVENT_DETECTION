import os
import time
import json
import atexit
import signal
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_socketio import SocketIO
import threading

# Import your existing modules
import detection as detect
import train_model
import preprocess
import audio

# Initialize Flask app and SocketIO
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'live-event-detection-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Share the socketio instance with detect module
detect.socketio = socketio

# Global state tracking
app_state = {
    'detection_running': False,
    'model_loaded': False,
    'preprocessing_running': False,
    'training_running': False,
    'recent_events': [],
    'preprocess_progress': 0,
    'training_progress': 0
}

# Main routes
@app.route('/')
def index():
    """Serve the main application page"""
    model_exists = os.path.exists(detect.MODEL_PATH)
    categories = []
    
    # Get available categories/classes
    if os.path.exists(detect.CATEGORIES_PATH):
        try:
            with open(detect.CATEGORIES_PATH, 'r') as f:
                categories_dict = json.load(f)
                categories = list(categories_dict.values())
        except:
            pass
            
    # Get available audio folders
    audio_folders = []
    if os.path.exists('audio'):
        audio_folders = [d for d in os.listdir('audio') if os.path.isdir(os.path.join('audio', d))]
    
    return render_template('main.html', 
                          model_exists=model_exists, 
                          app_state=app_state,
                          categories=categories,
                          audio_folders=audio_folders)

# Detection routes
@app.route('/detection')
def detection_page():
    """Serve the detection interface"""
    return render_template('detection.html')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    """Start the audio event detection"""
    if app_state['detection_running']:
        return jsonify({"success": False, "message": "Detection already running"})
    
    try:
        # Load the model if not already loaded
        if not app_state['model_loaded']:
            detect.load_trained_model()
            app_state['model_loaded'] = True
        
        # Start the detection
        detect.start_detection()
        app_state['detection_running'] = True
        
        # Emit status update to clients
        socketio.emit('status_update', {'detection_running': True})
        
        return jsonify({"success": True, "message": "Detection started"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error starting detection: {str(e)}"})

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    """Stop the audio event detection"""
    if not app_state['detection_running']:
        return jsonify({"success": False, "message": "Detection not running"})
    
    try:
        detect.stop_detection()
        app_state['detection_running'] = False
        
        # Emit status update to clients
        socketio.emit('status_update', {'detection_running': False})
        
        return jsonify({"success": True, "message": "Detection stopped"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error stopping detection: {str(e)}"})

@app.route('/test_detection', methods=['GET'])
def test_detection():
    """Trigger a test detection event"""
    try:
        detect.trigger_test_detection()
        return jsonify({"success": True, "message": "Test detection triggered"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error triggering test: {str(e)}"})

# Preprocessing routes
@app.route('/preprocess')
def preprocess_page():
    """Serve the preprocessing interface"""
    return render_template('preprocess.html')

def preprocess_task(source_dir, output_dir, frame_length, hop_length):
    """Run preprocessing in a separate thread"""
    try:
        app_state['preprocessing_running'] = True
        app_state['preprocess_progress'] = 0
        socketio.emit('status_update', {
            'preprocessing_running': True,
            'preprocess_progress': 0
        })
        
        # Define a progress callback
        def update_progress(progress):
            app_state['preprocess_progress'] = progress
            socketio.emit('preprocess_progress', {'progress': progress})
        
        # Run the preprocessing
        preprocess.process_audio_files(source_dir, output_dir, frame_length, hop_length, progress_callback=update_progress)
        
        app_state['preprocessing_running'] = False
        socketio.emit('status_update', {
            'preprocessing_running': False,
            'preprocess_progress': 100,
            'preprocess_complete': True
        })
    except Exception as e:
        app_state['preprocessing_running'] = False
        socketio.emit('status_update', {
            'preprocessing_running': False,
            'preprocess_error': str(e)
        })

@app.route('/start_preprocessing', methods=['POST'])
def start_preprocessing():
    """Start audio preprocessing"""
    if app_state['preprocessing_running']:
        return jsonify({"success": False, "message": "Preprocessing already running"})
    
    try:
        data = request.json
        source_dir = data.get('source_dir', 'audio')
        output_dir = data.get('output_dir', 'datasets')
        frame_length = int(data.get('frame_length', 1024))
        hop_length = int(data.get('hop_length', 512))
        
        # Create directories if they don't exist
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Start preprocessing in a separate thread
        thread = threading.Thread(
            target=preprocess_task,
            args=(source_dir, output_dir, frame_length, hop_length)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True, 
            "message": "Preprocessing started", 
            "source_dir": source_dir,
            "output_dir": output_dir
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error starting preprocessing: {str(e)}"})

# Training routes
@app.route('/train')
def train_page():
    """Serve the model training interface"""
    return render_template('train.html')

def training_task(dataset_dir, epochs, batch_size, validation_split):
    """Run model training in a separate thread"""
    try:
        app_state['training_running'] = True
        app_state['training_progress'] = 0
        socketio.emit('status_update', {
            'training_running': True,
            'training_progress': 0
        })
        
        # Define a progress callback
        def update_progress(epoch, total_epochs, logs=None):
            progress = int((epoch / total_epochs) * 100)
            app_state['training_progress'] = progress
            socketio.emit('training_progress', {
                'progress': progress,
                'epoch': epoch,
                'total_epochs': total_epochs,
                'logs': logs or {}
            })
        
        # Run the training
        train_model.train(
            dataset_dir=dataset_dir,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            progress_callback=update_progress
        )
        
        app_state['training_running'] = False
        socketio.emit('status_update', {
            'training_running': False,
            'training_progress': 100,
            'training_complete': True
        })
    except Exception as e:
        app_state['training_running'] = False
        socketio.emit('status_update', {
            'training_running': False,
            'training_error': str(e)
        })

@app.route('/start_training', methods=['POST'])
def start_training():
    """Start model training"""
    if app_state['training_running']:
        return jsonify({"success": False, "message": "Training already running"})
    
    try:
        data = request.json
        dataset_dir = data.get('dataset_dir', 'datasets')
        epochs = int(data.get('epochs', 20))
        batch_size = int(data.get('batch_size', 32))
        validation_split = float(data.get('validation_split', 0.2))
        
        # Ensure dataset directory exists
        if not os.path.exists(dataset_dir):
            return jsonify({"success": False, "message": f"Dataset directory {dataset_dir} does not exist"})
        
        # Start training in a separate thread
        thread = threading.Thread(
            target=training_task,
            args=(dataset_dir, epochs, batch_size, validation_split)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True, 
            "message": "Training started", 
            "epochs": epochs,
            "batch_size": batch_size
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error starting training: {str(e)}"})

# Audio recording routes
@app.route('/audio_recorder')
def audio_recorder():
    """Serve the audio recording interface"""
    return render_template('audio_recorder.html')

@app.route('/record_audio', methods=['POST'])
def record_audio():
    """Handle audio recording uploads"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    folder = request.form.get('folder', 'recordings')
    
    if not audio_file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Create audio directory if it doesn't exist
        audio_dir = 'audio'
        os.makedirs(audio_dir, exist_ok=True)
        
        folder_path = os.path.join(audio_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Generate a unique filename
        import uuid
        filename = f"{folder}_{uuid.uuid4().hex[:8]}.wav"
        file_path = os.path.join(folder_path, filename)
        
        audio_file.save(file_path)
        
        return jsonify({
            'success': True, 
            'file': filename, 
            'folder': folder,
            'path': file_path
        })
    except Exception as e:
        return jsonify({'error': f'Error saving audio: {str(e)}'}), 500

# Status API
@app.route('/status')
def get_status():
    """Get the current status of all components"""
    model_exists = os.path.exists(detect.MODEL_PATH)
    
    # Get audio categories if model exists
    categories = []
    if model_exists and os.path.exists(detect.CATEGORIES_PATH):
        try:
            with open(detect.CATEGORIES_PATH, 'r') as f:
                categories_dict = json.load(f)
                categories = list(categories_dict.values())
        except:
            pass
    
    # Get available audio folders
    audio_folders = []
    if os.path.exists('audio'):
        audio_folders = [d for d in os.listdir('audio') if os.path.isdir(os.path.join('audio', d))]
    
    # Check if datasets exist
    datasets_exist = os.path.exists('datasets')
    
    return jsonify({
        'detection_running': app_state['detection_running'],
        'model_loaded': app_state['model_loaded'],
        'model_exists': model_exists,
        'preprocessing_running': app_state['preprocessing_running'],
        'training_running': app_state['training_running'],
        'categories': categories,
        'audio_folders': audio_folders,
        'datasets_exist': datasets_exist,
        'recent_events': app_state['recent_events'][-10:] if app_state['recent_events'] else []
    })

# Static file routes
@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

# SocketIO events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    socketio.emit('status', {
        'detection_running': app_state['detection_running'],
        'model_loaded': app_state['model_loaded'],
        'preprocessing_running': app_state['preprocessing_running'],
        'training_running': app_state['training_running']
    })

@socketio.on('client_test')
def handle_client_test(data):
    """Handle test message from client"""
    print(f'Client test message: {data}')
    socketio.emit('server_test', {
        'message': 'Server received test message',
        'received_data': data,
        'time': time.time()
    })

# Handle detection events from detect.py
def handle_detection_event(data):
    """Process detection events from detect.py"""
    # Store in recent events
    app_state['recent_events'].append(data)
    if len(app_state['recent_events']) > 50:
        app_state['recent_events'] = app_state['recent_events'][-50:]
    
    # Forward to clients
    socketio.emit('detection_event', data)

# Register the handler with detect module
detect.register_detection_handler(handle_detection_event)

# Create a heartbeat emitter
def send_heartbeat():
    """Send regular heartbeat to clients"""
    while True:
        socketio.emit('heartbeat', {'time': time.time()})
        socketio.sleep(5)

# Main entry point
if __name__ == '__main__':
    # Make the 'templates' directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the static directory for CSS and JS files
    os.makedirs('static', exist_ok=True)
    
    # Register cleanup handlers
    atexit.register(detect.cleanup)
    signal.signal(signal.SIGINT, lambda sig, frame: detect.cleanup())
    
    try:
        # Start heartbeat thread
        socketio.start_background_task(send_heartbeat)
        
        # Start the server
        print("Starting server on http://127.0.0.1:4500")
        socketio.run(app, debug=True, host='0.0.0.0', port=4500)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        detect.cleanup()