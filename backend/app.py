"""
Flask Backend for the Standards Library Maintenance Tool
This application serves a REST API for the frontend to interact with.
"""
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS  # 1. Import the CORS library

from library_controller import LibraryController

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# Create a single, shared instance of our business logic controller
controller = LibraryController()

@app.route("/api/info", methods=["GET"])
def get_library_info():
    """
    A simple endpoint to get basic information about the library.
    """
    info = {
        "version": controller.get_library_version()
    }
    return jsonify(info)

@app.route("/api/standards", methods=["GET"])
def get_standards():
    """
    An endpoint to get a list of all standards in the library.
    """
    standards = controller.get_all_standards()
    return jsonify(standards)

@app.route("/api/standards", methods=["POST"])
def create_standard():
    """
    An endpoint to create a new standard. Expects a JSON body.
    """
    data = request.get_json()
    try:
        new_standard = controller.create_standard(data)
        return jsonify(new_standard), 201 # 201 Created
    except ValueError as e:
        # Return a 400 Bad Request error if validation fails
        return jsonify({"message": str(e)}), 400

@app.route("/api/clusters", methods=["GET"])
def get_clusters():
    """
    An endpoint to get a list of all valid clusters.
    """
    clusters = controller.get_all_clusters()
    return jsonify(clusters)

@app.route("/api/standards/<string:standard_id>", methods=["PUT"])
def update_standard_route(standard_id):
    """
    An endpoint to update an existing standard.
    """
    data = request.get_json()
    try:
        updated_standard = controller.update_standard(standard_id, data)
        return jsonify(updated_standard), 200 # 200 OK
    except ValueError as e:
        # Return a 400 Bad Request error if validation fails
        return jsonify({"message": str(e)}), 400

@app.route("/api/standards/<string:standard_id>", methods=["DELETE"])
def delete_standard_route(standard_id):
    """
    An endpoint to delete an existing standard.
    """
    if controller.delete_standard(standard_id):
        return jsonify({"message": "Standard deleted successfully"}), 200
    else:
        return jsonify({"message": "Standard not found"}), 404

# --- Backup & Restore Endpoints ---

@app.route("/api/backup", methods=["POST"])
def create_backup_route():
    """Creates a new timestamped backup of the library."""
    try:
        backup_filename = controller.create_backup()
        return jsonify({"message": "Backup created successfully", "filename": backup_filename}), 201
    except Exception as e:
        return jsonify({"message": f"Backup failed: {str(e)}"}), 500

@app.route("/api/backups", methods=["GET"])
def get_backups_route():
    """Returns a list of all available backup files."""
    files = controller.get_backup_files()
    return jsonify(files)

@app.route("/api/backups/<string:filename>", methods=["GET"])
def download_backup_route(filename):
    """Serves a specific backup file for download."""
    # Ask the controller for the correct backup directory path
    backup_dir = controller.file_manager.backups_dir
    return send_from_directory(backup_dir, filename, as_attachment=True)

@app.route("/api/backups/<string:filename>", methods=["DELETE"])
def delete_backup_route(filename):
    """Deletes a specific backup file."""
    if controller.delete_backup_file(filename):
        return jsonify({"message": "Backup deleted successfully"}), 200
    else:
        return jsonify({"message": "Backup file not found or could not be deleted"}), 404

@app.route("/api/restore", methods=["POST"])
def restore_from_backup_route():
    """Restores the library from an uploaded backup file."""
    if 'backup_file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    file = request.files['backup_file']
    if controller.restore_from_file(file):
        return jsonify({"message": "Library restored successfully"}), 200
    else:
        return jsonify({"message": "Restore failed. Invalid file or server error."}), 500

@app.route("/api/restore/<string:filename>", methods=["POST"])
def restore_from_server_backup_route(filename):
    """Restores the library from a specific backup file on the server."""
    if controller.restore_from_backup(filename):
        return jsonify({"message": "Library restored successfully"}), 200
    else:
        return jsonify({"message": "Restore failed. Backup file not found or server error."}), 500

# --- Import & Export Endpoints ---

@app.route("/api/export", methods=["POST"])
def export_library_route():
    """Exports the library with specified filters."""
    export_options = request.get_json()
    try:
        exported_data = controller.get_exported_data(export_options)
        return jsonify(exported_data), 200
    except Exception as e:
        return jsonify({"message": f"Export failed: {str(e)}"}), 500

@app.route("/api/import", methods=["POST"])
def import_library_route():
    """Imports clusters and standards from an uploaded JSON file."""
    if 'import_file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    file = request.files['import_file']
    try:
        report = controller.import_from_file(file)
        return jsonify(report), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

# --- Cluster Maintenance Endpoints ---

@app.route("/api/clusters", methods=["POST"])
def create_cluster_route():
    """Creates a new cluster."""
    data = request.get_json()
    try:
        new_cluster = controller.create_cluster(data)
        return jsonify(new_cluster), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@app.route("/api/clusters/<string:cluster_id>", methods=["PUT"])
def update_cluster_route(cluster_id):
    """Updates an existing cluster."""
    data = request.get_json()
    try:
        updated_cluster = controller.update_cluster(cluster_id, data)
        return jsonify(updated_cluster), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@app.route("/api/clusters/<string:cluster_id>", methods=["DELETE"])
def delete_cluster_route(cluster_id):
    """Deletes a cluster."""
    try:
        controller.delete_cluster(cluster_id)
        return jsonify({"message": "Cluster deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

# --- Static File Serving (for development) ---
# It's recommended to use a proper web server like Nginx or Caddy in production

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serves the static files for the frontend application.
    """
    frontend_folder = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    if path != "" and os.path.exists(os.path.join(frontend_folder, path)):
        return send_from_directory(frontend_folder, path)
    else:
        return send_from_directory(frontend_folder, 'index.html')