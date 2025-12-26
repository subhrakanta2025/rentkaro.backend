from app import db
from datetime import datetime
import uuid

class KYCVerification(db.Model):
    __tablename__ = 'kyc_verifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Aadhaar
    aadhaar_number = db.Column(db.String(20))
    aadhaar_verified = db.Column(db.Boolean, default=False)
    aadhaar_document_url = db.Column(db.String(255))
    
    # Driving License
    driving_license_number = db.Column(db.String(20))
    dl_verified = db.Column(db.Boolean, default=False)
    dl_document_url = db.Column(db.String(255))
    dl_expiry_date = db.Column(db.Date)
    selfie_document_url = db.Column(db.String(255))
    
    # PAN
    pan_number = db.Column(db.String(10))
    pan_verified = db.Column(db.Boolean, default=False)
    
    # Address Proof
    address_proof_type = db.Column(db.String(50))  # 'utility_bill', 'voter_id', 'passport', etc.
    address_proof_url = db.Column(db.String(255))
    address_verified = db.Column(db.Boolean, default=False)
    
    # Verification Status
    verification_status = db.Column(db.String(20), default='pending')  # 'pending', 'verified', 'rejected'
    rejection_reason = db.Column(db.Text)
    
    # Upload Status
    documents_uploaded = db.Column(db.Boolean, default=False)  # True when all 3 documents are uploaded
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
