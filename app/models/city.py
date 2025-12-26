import re
import uuid
from datetime import datetime

from app import db


def _slugify(value: str) -> str:
    """Create a URL-friendly slug from the provided city name."""
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return slug or str(uuid.uuid4())


class City(db.Model):
    __tablename__ = 'cities'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), unique=True, nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.slug = kwargs.get('slug') or _slugify(name)

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<City {self.name}>"
