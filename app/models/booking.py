from app import db
from datetime import datetime
import uuid

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    customer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'), nullable=False)
    agency_id = db.Column(db.String(36), db.ForeignKey('agencies.id'), nullable=False)
    
    # Booking Details
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    pickup_location = db.Column(db.String(255), nullable=False)
    dropoff_location = db.Column(db.String(255), nullable=False)
    
    # Pricing
    daily_rate = db.Column(db.Float, nullable=False)
    number_of_days = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    security_deposit = db.Column(db.Float, default=0)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # 'pending', 'confirmed', 'active', 'completed', 'cancelled'
    payment_status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'refunded'
    
    # Additional Details
    notes = db.Column(db.Text)
    odometer_start = db.Column(db.Integer)
    odometer_end = db.Column(db.Integer)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
