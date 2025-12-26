from app import db
from datetime import datetime
import uuid

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    razorpay_order_id = db.Column(db.String(100), nullable=False)
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(255))
    amount = db.Column(db.Integer, nullable=False)  # stored in paise
    currency = db.Column(db.String(10), default='INR')
    status = db.Column(db.String(50), default='created')  # created, paid, failed
    method = db.Column(db.String(50))
    email = db.Column(db.String(120))
    contact = db.Column(db.String(30))
    notes = db.Column(db.Text)
    raw_response = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
