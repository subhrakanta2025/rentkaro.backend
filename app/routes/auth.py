import base64
import json
import time
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User, Profile, UserRoleModel
from app.utils.mail import generate_otp, send_otp_email, send_activation_email, send_password_reset_email
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

RESET_LINK_TTL_SECONDS = 15 * 60


class ResetTokenError(Exception):
    """Base class for reset token errors."""


class ResetTokenInvalid(ResetTokenError):
    pass


class ResetTokenExpired(ResetTokenError):
    pass


def _generate_reset_token(email: str) -> str:
    payload = {
        'email': email,
        'timestamp': int(time.time())
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    return encoded.rstrip('=')


def _decode_reset_token(token: str) -> str:
    if not token:
        raise ResetTokenInvalid('Missing reset token')

    # Restore padding
    padded = token + '=' * (-len(token) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8')
        payload = json.loads(decoded)
    except Exception as exc:
        raise ResetTokenInvalid('Invalid reset token') from exc

    email = payload.get('email')
    timestamp = payload.get('timestamp')

    if not email or timestamp is None:
        raise ResetTokenInvalid('Invalid reset token payload')

    try:
        timestamp_value = float(timestamp)
    except (ValueError, TypeError) as exc:
        raise ResetTokenInvalid('Invalid timestamp in token') from exc

    if time.time() - timestamp_value > RESET_LINK_TTL_SECONDS:
        raise ResetTokenExpired('Reset link has expired')

    return email


def _build_reset_link(token: str) -> str:
    base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:8080')
    reset_path = f"{base_url.rstrip('/')}/reset-password?token={token}"
    return reset_path

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user and send OTP"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    email = data['email'].lower().strip()
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    try:
        user = User(email=email)
        user.set_password(data['password'])
        user.is_active = False  # Account not active until OTP verified
        
        # Generate and set OTP
        otp = generate_otp()
        user.otp_code = otp
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        db.session.add(user)
        db.session.flush()
        
        # Create profile
        profile = Profile(
            user_id=user.id,
            full_name=data.get('fullName', ''),
            phone=data.get('phone', '')
        )
        db.session.add(profile)
        
        # Create user role
        role = data.get('role', 'customer')
        user_role = UserRoleModel(user_id=user.id, role=role)
        db.session.add(user_role)
        
        db.session.commit()
        
        # Send OTP email
        send_otp_email(user.email, otp)
        
        return jsonify({
            'message': 'User registered successfully. OTP has been sent to your email.',
            'user': {
                'id': user.id,
                'email': user.email,
                'isActive': user.is_active
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/activate', methods=['POST'])
def activate_account():
    """Activate account with OTP"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('otp'):
        return jsonify({'error': 'Email and OTP are required'}), 400
    
    email = data['email'].lower().strip()
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.is_active:
        return jsonify({'error': 'Account is already activated'}), 400
    
    # Check OTP
    if user.otp_code != data['otp']:
        return jsonify({'error': 'Invalid OTP'}), 400
    
    # Check OTP expiry
    if datetime.utcnow() > user.otp_expires_at:
        return jsonify({'error': 'OTP has expired. Please register again.'}), 400
    
    try:
        user.is_active = True
        user.otp_code = None
        user.otp_expires_at = None
        
        db.session.commit()
        
        # Send activation confirmation email
        profile = Profile.query.filter_by(user_id=user.id).first()
        full_name = profile.full_name if profile else user.email.split('@')[0]
        send_activation_email(user.email, full_name)
        
        return jsonify({
            'message': 'Account activated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'isActive': user.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to email"""
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    email = data['email'].lower().strip()
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.is_active:
        return jsonify({'error': 'Account is already activated'}), 400
    
    try:
        # Generate new OTP
        otp = generate_otp()
        user.otp_code = otp
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        db.session.commit()
        
        # Send OTP email
        send_otp_email(user.email, otp)
        
        return jsonify({
            'message': 'OTP has been resent to your email'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send a signed reset link to the user's email"""
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        # Return success to avoid user enumeration
        return jsonify({'message': 'If an account exists for this email, a reset link has been sent.'}), 200

    if not user.is_active:
        return jsonify({'error': 'Please activate your account before resetting the password.'}), 400

    try:
        token = _generate_reset_token(user.email)
        reset_link = _build_reset_link(token)
        send_password_reset_email(user.email, reset_link)

        return jsonify({'message': 'Password reset instructions have been sent to your email.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/resend-reset-password', methods=['POST'])
def resend_reset_password():
    """Resend password reset link"""
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message': 'If an account exists for this email, a reset link has been sent.'}), 200

    if not user.is_active:
        return jsonify({'error': 'Please activate your account before resetting the password.'}), 400

    try:
        token = _generate_reset_token(user.email)
        reset_link = _build_reset_link(token)
        send_password_reset_email(user.email, reset_link)

        return jsonify({'message': 'A fresh reset link has been sent to your email.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using a signed token"""
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    new_password = data.get('password', '').strip()

    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'Password should be at least 6 characters long'}), 400

    try:
        email = _decode_reset_token(token)
    except ResetTokenExpired:
        return jsonify({'error': 'Reset link has expired. Please request a new one.'}), 400
    except ResetTokenInvalid:
        return jsonify({'error': 'Invalid reset link.'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'error': 'Invalid reset link.'}), 400

    if user.check_password(new_password):
        return jsonify({'error': 'New password cannot be the same as your current password'}), 400

    try:
        user.set_password(new_password)
        db.session.commit()

        return jsonify({'message': 'Password has been reset successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    email = data['email'].lower().strip()
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is not activated. Please verify your email.'}), 403
    
    access_token = create_access_token(identity=user.id)
    
    user_role = UserRoleModel.query.filter_by(user_id=user.id).first()
    
    profile = Profile.query.filter_by(user_id=user.id).first()

    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user_role.role if user_role else 'customer',
            'profile': {
                'fullName': profile.full_name if profile else '',
                'phone': profile.phone if profile else '',
                'avatarUrl': profile.avatar_url if profile else None,
                'avatarLocked': profile.avatar_locked if profile else False,
            },
            'canListVehicles': bool(user.agency)
        },
        'access_token': access_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side should delete token)"""
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    user_role = UserRoleModel.query.filter_by(user_id=user_id).first()
    
    return jsonify({
        'user': {
            'id': user.id,
            'email': user.email,
            'isActive': user.is_active,
            'role': user_role.role if user_role else 'customer',
            'profile': {
                'fullName': profile.full_name if profile else '',
                'phone': profile.phone if profile else '',
                'avatarUrl': profile.avatar_url if profile else None,
                'avatarLocked': profile.avatar_locked if profile else False,
            },
            'canListVehicles': bool(user.agency)
        }
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Refresh access token"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/send-otp-email', methods=['POST'])
def send_otp_email_endpoint():
    """Send OTP to email for verification (without login)"""
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    email = data['email'].lower().strip()
    
    try:
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP temporarily (in a real app, use Redis or similar)
        # For now, we'll store in a temporary dict or cache
        from app import mail_cache
        mail_cache[email] = {
            'otp': otp,
            'expires_at': datetime.utcnow() + timedelta(minutes=10)
        }
        
        # Send OTP email
        send_otp_email(email, otp)
        
        return jsonify({
            'message': 'OTP sent to your email',
            'email': email
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-email-otp', methods=['POST'])
def verify_email_otp():
    """Verify OTP sent to email"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('otp'):
        return jsonify({'error': 'Email and OTP are required'}), 400
    
    email = data['email'].lower().strip()
    otp = data['otp']
    
    try:
        from app import mail_cache
        
        if email not in mail_cache:
            return jsonify({'error': 'No OTP found for this email. Please request a new OTP.'}), 400
        
        cached = mail_cache[email]
        
        # Check OTP expiry
        if datetime.utcnow() > cached['expires_at']:
            del mail_cache[email]
            return jsonify({'error': 'OTP has expired. Please request a new OTP.'}), 400
        
        # Check OTP
        if cached['otp'] != otp:
            return jsonify({'error': 'Invalid OTP'}), 400
        
        # Clear the OTP from cache
        del mail_cache[email]
        
        return jsonify({
            'message': 'Email verified successfully',
            'verified': True,
            'email': email
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'access_token': access_token
    }), 200
