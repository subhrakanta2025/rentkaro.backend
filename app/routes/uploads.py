from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid

uploads_bp = Blueprint('uploads', __name__, url_prefix='/api/uploads')

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'pdf', 'avif'}

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

    upload_dir = current_app.config.get('UPLOAD_DIR')
    vehicle_folder = os.path.join(upload_dir, 'vehicles', str(user_id))
    os.makedirs(vehicle_folder, exist_ok=True)

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
                    filepath = os.path.join(vehicle_folder, secure_filename(filename))
                    file.save(filepath)
                    public_url = f"/uploads/vehicles/{user_id}/{filename}"
                    # Return absolute URL so frontend on different origin can render images
                    absolute_url = f"{request.host_url.rstrip('/')}{public_url}"
                    files_response.append({
                        'field': field_name,
                        'filename': filename,
                        'url': absolute_url
                    })

        return jsonify({'files': files_response}), 201
    except Exception as e:
        current_app.logger.exception('Failed to save uploaded files: %s', e)
        return jsonify({'error': str(e)}), 500
