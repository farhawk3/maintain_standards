"""
Flask Backend for the Standards Library Maintenance Tool
This application serves a REST API for the frontend to interact with.
"""
import os
import json
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix
from library_controller import LibraryController

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key") # Change in production
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)

# Auth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Load Users
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f).get('users', {})
    return {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
             return jsonify({"message": "Authentication required"}), 401
        user_email = session['user'].get('email')
        users = load_users()
        if users.get(user_email) != 'admin':
             return jsonify({"message": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Create a single, shared instance of our business logic controller
controller = LibraryController()

# --- Auth Routes ---

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def authorize():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        user_info = google.userinfo()
    
    # Check if user is allowed
    users = load_users()
    email = user_info.get('email')
    
    if email in users:
        session['user'] = user_info
        session['role'] = users[email]
        return redirect('/') # Redirect to home page
    else:
        return jsonify({"message": "User not authorized"}), 403

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect('/')

@app.route('/api/user')
def get_current_user():
    user = session.get('user')
    role = session.get('role')
    if user:
        return jsonify({"user": user, "role": role})
    return jsonify({"user": None, "role": None})

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
@login_required
def get_standards():
    """
    An endpoint to get a list of all standards in the library.
    """
    standards = controller.get_all_standards()
    return jsonify(standards)

@app.route("/api/standards", methods=["POST"])
@admin_required
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
@login_required
def get_clusters():
    """
    An endpoint to get a list of all valid clusters.
    """
    clusters = controller.get_all_clusters()
    return jsonify(clusters)

@app.route("/api/standards/<string:standard_id>", methods=["PUT"])
@admin_required
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
@admin_required
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
@admin_required
def create_backup_route():
    """Creates a new timestamped backup of the library."""
    try:
        backup_filename = controller.create_backup()
        return jsonify({"message": "Backup created successfully", "filename": backup_filename}), 201
    except Exception as e:
        return jsonify({"message": f"Backup failed: {str(e)}"}), 500

@app.route("/api/backups", methods=["GET"])
@admin_required
def get_backups_route():
    """Returns a list of all available backup files."""
    files = controller.get_backup_files()
    return jsonify(files)

@app.route("/api/backups/<string:filename>", methods=["GET"])
@admin_required
def download_backup_route(filename):
    """Serves a specific backup file for download."""
    # Ask the controller for the correct backup directory path
    backup_dir = controller.file_manager.backups_dir
    return send_from_directory(backup_dir, filename, as_attachment=True)

@app.route("/api/backups/<string:filename>", methods=["DELETE"])
@admin_required
def delete_backup_route(filename):
    """Deletes a specific backup file."""
    if controller.delete_backup_file(filename):
        return jsonify({"message": "Backup deleted successfully"}), 200
    else:
        return jsonify({"message": "Backup file not found or could not be deleted"}), 404

@app.route("/api/restore", methods=["POST"])
@admin_required
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
@admin_required
def restore_from_server_backup_route(filename):
    """Restores the library from a specific backup file on the server."""
    if controller.restore_from_backup(filename):
        return jsonify({"message": "Library restored successfully"}), 200
    else:
        return jsonify({"message": "Restore failed. Backup file not found or server error."}), 500

# --- Import & Export Endpoints ---

@app.route("/api/export", methods=["POST"])
@login_required
def export_library_route():
    """Exports the library with specified filters."""
    export_options = request.get_json()
    try:
        exported_data = controller.get_exported_data(export_options)
        return jsonify(exported_data), 200
    except Exception as e:
        return jsonify({"message": f"Export failed: {str(e)}"}), 500

@app.route("/api/import", methods=["POST"])
@admin_required
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
@admin_required
def create_cluster_route():
    """Creates a new cluster."""
    data = request.get_json()
    try:
        new_cluster = controller.create_cluster(data)
        return jsonify(new_cluster), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@app.route("/api/clusters/<string:cluster_id>", methods=["PUT"])
@admin_required
def update_cluster_route(cluster_id):
    """Updates an existing cluster."""
    data = request.get_json()
    try:
        updated_cluster = controller.update_cluster(cluster_id, data)
        return jsonify(updated_cluster), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@app.route("/api/clusters/<string:cluster_id>", methods=["DELETE"])
@admin_required
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