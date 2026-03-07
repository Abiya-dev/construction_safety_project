import os
import glob
from flask import Flask, render_template, Response, request, redirect, url_for, send_from_directory
from ultralytics import YOLO
from utils.frame_extractor import generate_frames, get_global_status

app = Flask(__name__)

# --- ABSOLUTE PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
REPORT_FOLDER = os.path.join(BASE_DIR, 'static', 'reports')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORT_FOLDER'] = REPORT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# Load Models
model_main = YOLO('models/yolo/best.pt')
model_gloves = YOLO('models/yolo/gloves.pt')

@app.route('/')
def index():
    # Fetch all PDF reports (Changed from CSV to PDF)
    report_files = glob.glob(os.path.join(app.config['REPORT_FOLDER'], '*.pdf'))
    # Sort by newest first
    report_files.sort(key=os.path.getmtime, reverse=True)
    report_names = [os.path.basename(f) for f in report_files]
    
    print(f"DEBUG: Found {len(report_names)} PDF reports in {app.config['REPORT_FOLDER']}")
    
    video_path = request.args.get('video_path')
    return render_template('index.html', reports=report_names, video_path=video_path)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return redirect(url_for('index'))
    file = request.files['video']
    if file.filename == '':
        return redirect(url_for('index'))
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return redirect(url_for('index', video_path=file.filename))

@app.route('/video_feed/<filename>')
def video_feed(filename):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return Response(generate_frames(model_main, model_gloves, video_path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return get_global_status()

@app.route('/download_report/<filename>')
def download_report(filename):
    # Sends the PDF as a downloadable attachment
    return send_from_directory(app.config['REPORT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
