from app import db
from datetime import datetime
import uuid

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    agency_id = db.Column(db.String(36), db.ForeignKey('agencies.id'))
    
    # Basic Info
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    vin = db.Column(db.String(100), unique=True)
    
    # Details
    vehicle_type = db.Column(db.String(50), nullable=False)  # 'car', 'bike', 'scooter', etc.
    fuel_type = db.Column(db.String(20), nullable=False)  # 'petrol', 'diesel', 'electric', etc.
    transmission = db.Column(db.String(20))  # 'manual', 'automatic'
    color = db.Column(db.String(50))
    mileage = db.Column(db.Integer)  # in km
    seating_capacity = db.Column(db.Integer)
    # Additional specifications
    displacement = db.Column(db.String(50))
    top_speed = db.Column(db.String(50))
    fuel_capacity = db.Column(db.String(50))
    weight = db.Column(db.String(50))
    late_fee_per_hr = db.Column(db.Float)
    excess_per_km = db.Column(db.Float)
    timings = db.Column(db.String(100))
    
    # Pricing
    daily_rate = db.Column(db.Float, nullable=False)
    weekly_rate = db.Column(db.Float)
    monthly_rate = db.Column(db.Float)
    security_deposit = db.Column(db.Float)
    
    # Status
    is_available = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='available')  # 'available', 'booked', 'maintenance'
    
    # Documents
    insurance_number = db.Column(db.String(100))
    insurance_expiry = db.Column(db.Date)
    registration_expiry = db.Column(db.Date)
    pollution_certificate_number = db.Column(db.String(100))
    pollution_expiry = db.Column(db.Date)
    
    # Location
    location = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('VehicleImage', backref='vehicle', cascade='all, delete-orphan')
    documents = db.relationship('VehicleDocument', backref='vehicle', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='vehicle', cascade='all, delete-orphan')

class VehicleImage(db.Model):
    __tablename__ = 'vehicle_images'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    image_type = db.Column(db.String(50))  # 'front', 'back', 'side', 'interior', etc.
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VehicleDocument(db.Model):
    __tablename__ = 'vehicle_documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'registration', 'insurance', 'pollution', etc.
    document_url = db.Column(db.String(255), nullable=False)
    expiry_date = db.Column(db.Date)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
