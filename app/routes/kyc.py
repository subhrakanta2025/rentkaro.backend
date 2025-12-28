from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
import base64
from app import db
from app.models.kyc import KYCVerification
from app.models.user import Profile

kyc_bp = Blueprint('kyc', __name__, url_prefix='/api/kyc')

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    base_upload = current_app.config.get('UPLOAD_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads'))
    kyc_folder = os.path.join(base_upload, 'kyc')
    return kyc_folder

def ensure_upload_folder():
    folder = get_upload_folder()
    os.makedirs(folder, exist_ok=True)
    return folder

@kyc_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_kyc_document():
    """Upload KYC document (Aadhaar, DL, or Selfie)"""
    user_id = get_jwt_identity()
    ensure_upload_folder()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    doc_type = request.form.get('docType')  # 'aadhaar', 'dl', 'selfie'
    
    if not doc_type or doc_type not in ['aadhaar', 'dl', 'selfie']:
        return jsonify({'error': 'Invalid document type'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    if len(file.read()) > MAX_FILE_SIZE:
        file.seek(0)
        return jsonify({'error': 'File size exceeds limit'}), 400
    
    file.seek(0)
    
    try:
        upload_folder = ensure_upload_folder()
        # Create unique filename
        filename = f"{user_id}_{doc_type}_{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
        filepath = os.path.join(upload_folder, filename)
        
        # Save file
        file.save(filepath)
        
        # Get or create KYC record
        kyc = KYCVerification.query.filter_by(user_id=user_id).first()
        if not kyc:
            kyc = KYCVerification(user_id=user_id)
            db.session.add(kyc)
            db.session.flush()
        
        # If uploading Aadhaar and it's a fresh start (no Aadhaar URL exists yet),
        # clear DL and Selfie from previous session to start fresh
        if doc_type == 'aadhaar' and not kyc.aadhaar_document_url:
            print(f"[KYC] Fresh upload session detected, clearing old DL and Selfie")
            # Delete old DL file
            if kyc.dl_document_url:
                try:
                    old_dl_filename = kyc.dl_document_url.split('/')[-1]
                    old_dl_filepath = os.path.join(ensure_upload_folder(), old_dl_filename)
                    if os.path.exists(old_dl_filepath):
                        os.remove(old_dl_filepath)
                        print(f"[KYC] Deleted old DL file: {old_dl_filename}")
                except Exception as e:
                    print(f"[KYC] Error deleting old DL file: {str(e)}")
            
            # Delete old Selfie file
            if kyc.selfie_document_url:
                try:
                    old_selfie_filename = kyc.selfie_document_url.split('/')[-1]
                    old_selfie_filepath = os.path.join(ensure_upload_folder(), old_selfie_filename)
                    if os.path.exists(old_selfie_filepath):
                        os.remove(old_selfie_filepath)
                        print(f"[KYC] Deleted old Selfie file: {old_selfie_filename}")
                except Exception as e:
                    print(f"[KYC] Error deleting old Selfie file: {str(e)}")
            
            # Clear the URLs from database
            kyc.dl_document_url = None
            kyc.selfie_document_url = None
            kyc.documents_uploaded = False
        
        # Update the appropriate document URL
        document_url = f"/uploads/kyc/{filename}"
        
        # Clear old document and file before updating with new one
        old_url = None
        if doc_type == 'aadhaar':
            old_url = kyc.aadhaar_document_url
            kyc.aadhaar_document_url = document_url
        elif doc_type == 'dl':
            old_url = kyc.dl_document_url
            kyc.dl_document_url = document_url
        elif doc_type == 'selfie':
            old_url = kyc.selfie_document_url
            kyc.selfie_document_url = document_url
            # Also update profile avatar
            profile = Profile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = Profile(user_id=user_id)
                db.session.add(profile)
            profile.avatar_url = document_url
            profile.avatar_locked = True
        
        # Delete old file if exists
        if old_url:
            try:
                old_filename = old_url.split('/')[-1]
                old_filepath = os.path.join(ensure_upload_folder(), old_filename)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
                    print(f"[KYC] Deleted old {doc_type} file: {old_filename}")
            except Exception as e:
                print(f"[KYC] Error deleting old file: {str(e)}")
        
        # Commit first to ensure the record is saved
        db.session.commit()
        
        # Refresh from database to get latest values
        db.session.refresh(kyc)
        
        # Debug: Print raw values
        print(f"[KYC Raw Values] Aadhaar: {repr(kyc.aadhaar_document_url)}, DL: {repr(kyc.dl_document_url)}, Selfie: {repr(kyc.selfie_document_url)}")
        
        # Check if all documents are uploaded - must have all 3 non-empty URLs
        # Each URL must be a non-empty string
        has_aadhaar = kyc.aadhaar_document_url is not None and str(kyc.aadhaar_document_url).strip() != ''
        has_dl = kyc.dl_document_url is not None and str(kyc.dl_document_url).strip() != ''
        has_selfie = kyc.selfie_document_url is not None and str(kyc.selfie_document_url).strip() != ''
        
        print(f"[KYC Boolean Checks] Aadhaar: {has_aadhaar}, DL: {has_dl}, Selfie: {has_selfie}")
        
        # All uploaded only if ALL 3 are present
        all_uploaded = has_aadhaar and has_dl and has_selfie
        
        # Update the documents_uploaded flag
        kyc.documents_uploaded = all_uploaded
        db.session.commit()
        
        print(f"[KYC Upload Debug] User: {user_id}, DocType: {doc_type}, AllUploaded: {all_uploaded}")
        print(f"[KYC Progress] Aadhaar: {has_aadhaar}, DL: {has_dl}, Selfie: {has_selfie}")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'documentUrl': document_url,
            'docType': doc_type,
            'documentsUploaded': all_uploaded,
            'verificationStatus': kyc.verification_status,
            'progress': {
                'aadhaar': has_aadhaar,
                'dl': has_dl,
                'selfie': has_selfie
            },
            'debug': {
                'aadhaarUrl': kyc.aadhaar_document_url,
                'dlUrl': kyc.dl_document_url,
                'selfieUrl': kyc.selfie_document_url
            }
        }), 200
        
    except Exception as e:
        import traceback
        db.session.rollback()
        tb = traceback.format_exc()
        try:
            current_app.logger.error('[KYC Upload] Exception: %s\n%s', str(e), tb)
        except Exception:
            print('[KYC Upload] Exception:', str(e))
            print(tb)
        return jsonify({'error': 'Internal server error'}), 500


@kyc_bp.route('/status', methods=['GET'])
@jwt_required()
def get_kyc_status():
    """Get KYC verification status"""
    user_id = get_jwt_identity()
    
    kyc = KYCVerification.query.filter_by(user_id=user_id).first()
    
    if not kyc:
        return jsonify({
            'kyc': {
                'verificationStatus': 'pending',
                'aadhaarVerified': False,
                'dlVerified': False,
                'panVerified': False,
                'addressVerified': False,
                'documentsUploaded': False
            }
        }), 200
    
    return jsonify({
        'kyc': {
            'id': kyc.id,
            'userId': user_id,
            'aadhaarNumber': kyc.aadhaar_number,
            'aadhaarVerified': kyc.aadhaar_verified,
            'drivingLicenseNumber': kyc.driving_license_number,
            'dlVerified': kyc.dl_verified,
            'dlExpiryDate': kyc.dl_expiry_date.isoformat() if kyc.dl_expiry_date else None,
            'panNumber': kyc.pan_number,
            'panVerified': kyc.pan_verified,
            'addressProofType': kyc.address_proof_type,
            'addressVerified': kyc.address_verified,
            'aadhaarDocumentUrl': kyc.aadhaar_document_url,
            'dlDocumentUrl': kyc.dl_document_url,
            'selfieUrl': kyc.selfie_document_url,
            'verificationStatus': kyc.verification_status,
            'rejectionReason': kyc.rejection_reason,
            'documentsUploaded': kyc.documents_uploaded,
            'debug': {
                'aadhaarUrl': kyc.aadhaar_document_url,
                'dlUrl': kyc.dl_document_url,
                'selfieUrl': kyc.selfie_document_url,
                'rawAadhaar': repr(kyc.aadhaar_document_url),
                'rawDl': repr(kyc.dl_document_url),
                'rawSelfie': repr(kyc.selfie_document_url)
            }
        }
    }), 200

@kyc_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_kyc():
    """Submit KYC verification documents"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        kyc = KYCVerification.query.filter_by(user_id=user_id).first()
        
        if not kyc:
            kyc = KYCVerification(user_id=user_id)
            db.session.add(kyc)
            db.session.flush()

        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = Profile(user_id=user_id)
            db.session.add(profile)
        
        # Update Aadhaar details
        if 'aadhaarNumber' in data:
            kyc.aadhaar_number = data['aadhaarNumber']
            kyc.aadhaar_document_url = data.get('aadhaarDocumentUrl')
        
        # Update DL details
        if 'drivingLicenseNumber' in data:
            kyc.driving_license_number = data['drivingLicenseNumber']
            kyc.dl_document_url = data.get('dlDocumentUrl')
            kyc.dl_expiry_date = data.get('dlExpiryDate')
        
        if 'selfieUrl' in data:
            kyc.selfie_document_url = data['selfieUrl']
            profile.avatar_url = data['selfieUrl']
            profile.avatar_locked = True

        # Update PAN details
        if 'panNumber' in data:
            kyc.pan_number = data['panNumber']
        
        # Update address proof
        if 'addressProofType' in data:
            kyc.address_proof_type = data['addressProofType']
            kyc.address_proof_url = data.get('addressProofUrl')
        
        kyc.verification_status = 'pending'
        
        db.session.commit()
        
        return jsonify({
            'message': 'KYC documents submitted for verification',
            'kyc': {'id': kyc.id}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kyc_bp.route('/verify/<kyc_id>', methods=['PUT'])
@jwt_required()
def verify_kyc(kyc_id):
    """Verify KYC (Admin only)"""
    # This endpoint should be protected by admin role check
    data = request.get_json()
    
    kyc = KYCVerification.query.get(kyc_id)
    if not kyc:
        return jsonify({'error': 'KYC record not found'}), 404
    
    try:
        kyc.aadhaar_verified = data.get('aadhaarVerified', kyc.aadhaar_verified)
        kyc.dl_verified = data.get('dlVerified', kyc.dl_verified)
        kyc.pan_verified = data.get('panVerified', kyc.pan_verified)
        kyc.address_verified = data.get('addressVerified', kyc.address_verified)
        kyc.verification_status = data.get('verificationStatus', 'pending')
        kyc.rejection_reason = data.get('rejectionReason')
        
        db.session.commit()
        
        return jsonify({'message': 'KYC verified successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kyc_bp.route('/debug/reset', methods=['POST'])
@jwt_required()
def reset_kyc_debug():
    """Debug endpoint to reset KYC uploads - FOR TESTING ONLY"""
    user_id = get_jwt_identity()
    
    try:
        kyc = KYCVerification.query.filter_by(user_id=user_id).first()
        if kyc:
            kyc.aadhaar_document_url = None
            kyc.dl_document_url = None
            kyc.selfie_document_url = None
            kyc.documents_uploaded = False
            db.session.commit()
            return jsonify({'message': 'KYC data reset'}), 200
        return jsonify({'error': 'No KYC record found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
