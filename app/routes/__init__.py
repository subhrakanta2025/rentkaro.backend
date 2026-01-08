# Routes package
from .auth import auth_bp
from .users import users_bp
from .vehicles import vehicles_bp
from .bookings import bookings_bp
from .agencies import agencies_bp
from .agency_kyc import agency_kyc_bp
from .kyc import kyc_bp

__all__ = [
    'auth_bp',
    'users_bp',
    'vehicles_bp',
    'bookings_bp',
    'agencies_bp',
    'agency_kyc_bp',
    'kyc_bp'
]
