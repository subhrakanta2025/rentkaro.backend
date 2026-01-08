from app import db
from datetime import datetime
from enum import Enum
import uuid

class UserRole(Enum):
    CUSTOMER = 'customer'
    AGENCY = 'agency'
    ADMIN = 'admin'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    # Social login fields
    provider = db.Column(db.String(50), nullable=True)
    provider_id = db.Column(db.String(255), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=False)  # Account activation status
    otp_code = db.Column(db.String(6), nullable=True)  # 6-digit OTP
    otp_expires_at = db.Column(db.DateTime, nullable=True)  # OTP expiry time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    user_role = db.relationship('UserRoleModel', backref='user', uselist=False, cascade='all, delete-orphan')
    kyc_verification = db.relationship('KYCVerification', backref='user', uselist=False, cascade='all, delete-orphan')
    vehicles = db.relationship('Vehicle', backref='owner', cascade='all, delete-orphan')
    bookings_as_customer = db.relationship('Booking', foreign_keys='Booking.customer_id', backref='customer', cascade='all, delete-orphan')
    agency = db.relationship('Agency', foreign_keys='Agency.user_id', primaryjoin='User.id==Agency.user_id', backref='owner', uselist=False, cascade='all, delete-orphan')
    managed_agencies = db.relationship('Agency', foreign_keys='Agency.admin_user_id', primaryjoin='User.id==Agency.admin_user_id', backref='admin', cascade='all, delete-orphan')
    password_reset_requests = db.relationship(
        'PasswordResetRequest',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(255))
    avatar_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserRoleModel(db.Model):
    __tablename__ = 'user_roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False)  # 'customer', 'agency', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
