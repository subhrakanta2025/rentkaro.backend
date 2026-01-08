from app import db
from datetime import datetime
import uuid

class AgencyKYC(db.Model):
    __tablename__ = 'agency_kyc'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agency_id = db.Column(db.String(36), db.ForeignKey('agencies.id'), nullable=False, unique=True)

    pan_number = db.Column(db.String(20))
    gst_number = db.Column(db.String(20))
    license_number = db.Column(db.String(50))

    pan_doc_url = db.Column(db.String(255))
    gst_doc_url = db.Column(db.String(255))
    license_doc_url = db.Column(db.String(255))

    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    pan_verified = db.Column(db.Boolean, default=False)
    gst_verified = db.Column(db.Boolean, default=False)
    license_verified = db.Column(db.Boolean, default=False)
    rejection_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'agencyId': self.agency_id,
            'panNumber': self.pan_number,
            'gstNumber': self.gst_number,
            'licenseNumber': self.license_number,
            'panDocUrl': self.pan_doc_url,
            'gstDocUrl': self.gst_doc_url,
            'licenseDocUrl': self.license_doc_url,
            'verificationStatus': self.verification_status,
            'panVerified': self.pan_verified,
            'gstVerified': self.gst_verified,
            'licenseVerified': self.license_verified,
            'rejectionReason': self.rejection_reason,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }
