from app import db
from datetime import datetime
import uuid

class Agency(db.Model):
    __tablename__ = 'agencies'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)  # Agency owner/manager
    admin_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)  # Admin who created/manages this agency
    
    # Agency Details
    agency_name = db.Column(db.String(120), nullable=False)
    business_type = db.Column(db.String(50))  # 'individual', 'partnership', 'company'
    registration_number = db.Column(db.String(100), unique=True)
    gst_number = db.Column(db.String(15))
    pan_number = db.Column(db.String(10))
    
    # Contact
    agency_phone = db.Column(db.String(20))
    agency_email = db.Column(db.String(120))
    gst_doc_url = db.Column(db.String(255))
    business_photo_url = db.Column(db.String(255))
    
    # Location
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Bank Details
    bank_account_number = db.Column(db.String(20))
    bank_ifsc_code = db.Column(db.String(11))
    bank_account_holder_name = db.Column(db.String(120))
    
    # Status
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Statistics
    total_vehicles = db.Column(db.Integer, default=0)
    total_bookings = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Float, default=0)
    average_rating = db.Column(db.Float, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
