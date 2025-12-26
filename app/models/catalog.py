from app import db
from datetime import datetime
import uuid


class CatalogBrand(db.Model):
    __tablename__ = 'catalog_brands'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    vehicle_type = db.Column(db.String(20), nullable=False)  # 'bike' or 'car'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    models = db.relationship('CatalogModel', backref='brand', cascade='all, delete-orphan')


class CatalogModel(db.Model):
    __tablename__ = 'catalog_models'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id = db.Column(db.String(36), db.ForeignKey('catalog_brands.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('brand_id', 'name', name='uq_brand_model'),
    )
