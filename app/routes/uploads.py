from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid

# Attempt to import GCS client; if missing, defer error until runtime and allow app to start.
try:
    from google.cloud import storage  # type: ignore
    _gcs_available = True
except Exception as _e:
    storage = None
    _gcs_available = False

uploads_bp = Blueprint('uploads', __name__, url_prefix='/api/uploads')

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'pdf', 'avif'}

GCS_BUCKET = os.getenv('GCS_BUCKET')
GCS_SERVICE_ACCOUNT_FILE = os.getenv('GCS_SERVICE_ACCOUNT_FILE', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'leafy-guide-474311-u3-0328c0e70b35.json'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@uploads_bp.route('', methods=['POST'])
@jwt_required()
def upload_files():
    """Accept multipart/form-data uploads and store files under uploads/vehicles/<user_id>/ and return public URLs."""
    user_id = get_jwt_identity()
    if 'files' not in request.files and len(request.files) == 0:
        # allow arbitrary field names
        pass

    if not _gcs_available:
        return jsonify({'error': 'GCS client library not installed. Run the app with the project virtualenv or install google-cloud-storage.'}), 500

    if not GCS_BUCKET:
        return jsonify({'error': 'GCS_BUCKET is not configured'}), 500

    if GCS_SERVICE_ACCOUNT_FILE and os.path.exists(GCS_SERVICE_ACCOUNT_FILE):
        client = storage.Client.from_service_account_json(GCS_SERVICE_ACCOUNT_FILE)
    else:
        client = storage.Client()

    bucket = client.bucket(GCS_BUCKET)

    files_response = []
    try:
        for field_name in request.files:
            file_storage = request.files.getlist(field_name)
            for file in file_storage:
                if file and file.filename:
                    if not allowed_file(file.filename):
                        return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"{field_name}_{uuid.uuid4().hex}.{ext}"
                    blob_path = f"vehicles/{user_id}/{secure_filename(filename)}"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_file(file, content_type=file.mimetype)
                    blob.make_public()
                    absolute_url = blob.public_url
                    files_response.append({
                        'field': field_name,
                        'filename': filename,
                        'url': absolute_url
                    })

        return jsonify({'files': files_response}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
