from app import db
from datetime import datetime
import uuid


class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    agency_id = db.Column(db.String(36), db.ForeignKey('agencies.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'bookingId': self.booking_id,
            'customerId': self.customer_id,
            'agencyId': self.agency_id,
            'rating': self.rating,
            'comment': self.comment,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
