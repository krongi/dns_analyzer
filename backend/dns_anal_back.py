from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import os
import json
import subprocess

def read_progress():
    progress_file = "progress.json"
    if not os.path.exists(progress_file) or os.path.getsize(progress_file) == 0:
        return {"status": "idle", "progress": 0, "message": "Awaiting file."}
    try:
        with open(progress_file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"status": "idle", "progress": 0, "message": "Awaiting file."}

app = Flask(__name__)
CORS(app, origins="*")

UPLOAD_FOLDER = "/app/uploads"
RESULT_FOLDER = "/app/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

log_file_name = None

def process_log_file(filename):
    """Process the log file asynchronously"""
    log_file_path = os.path.join(UPLOAD_FOLDER, str(filename))
    if not os.path.exists(log_file_path):
        print(f"Error: Log file {log_file_path} does not exist!")
        return
    print(f"Processing log file: {log_file_path}")
    subprocess.run(["python3", "dns_anal_function.py", log_file_path], check=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads"""
    global log_file_name
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    log_file_name = file.filename

    return jsonify({"message": "File uploaded successfully", "path": log_file_name})

@app.route("/processed-results", methods=["GET"])
def get_processed_result():
    """Fetch the content of a specific processed result file"""
    filename = request.args.get("file")  # Get filename from request
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    file_path = os.path.join(RESULT_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    with open(file_path, "r") as file:
        content = json.load(file)  # Read JSON content
    return jsonify(content)  # ✅ Now only returns the selected file's JSON


@app.route("/start-processing", methods=["POST"])
def start_processing():
    filename = request.data.decode('utf-8')
    print(f"Processing file: {filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    # process the file...
    try:
        threading.Thread(target=process_log_file, args=(log_file_name,)).start()
        return jsonify({"message": "Processing started"})
    except:
        return jsonify({"error": str(e)}), 500

   
@app.route("/progress", methods=["GET"])
def progress():
    """Get processing progress"""
    return jsonify(read_progress())

@app.route("/results", methods=["GET"])
def list_results():
    """Return a list of processed files sorted by most recent"""
    result_files = sorted(
        [f for f in os.listdir(RESULT_FOLDER) if os.path.isfile(os.path.join(RESULT_FOLDER, f))],
        key=lambda x: os.path.getmtime(os.path.join(RESULT_FOLDER, x)),
        reverse=True
    )
    print("Serving result filenames:", result_files)  
    return jsonify({"files": result_files}) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")