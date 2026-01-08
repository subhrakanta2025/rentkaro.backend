from app import db
from datetime import datetime
import uuid


class Favorite(db.Model):
    __tablename__ = 'favorites'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'vehicle_id', name='uq_favorites_user_vehicle'),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

