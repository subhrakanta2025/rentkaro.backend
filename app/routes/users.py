from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, Profile

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


def _build_profile_payload(user, profile):
    vehicles = user.vehicles or []
    bookings = user.bookings_as_customer or []
    agency = user.agency
    loyalty_score = min(100, 45 + len(bookings) * 4)
    next_milestone = max(0, 5 - (len(bookings) % 5)) if bookings else 5

    agency_details = None
    if agency:
        agency_details = {
            'id': agency.id,
            'agencyName': agency.agency_name,
            'businessType': agency.business_type,
            'registrationNumber': agency.registration_number,
            'gstNumber': agency.gst_number,
            'panNumber': agency.pan_number,
            'agencyPhone': agency.agency_phone,
            'agencyEmail': agency.agency_email,
            'address': agency.address,
            'city': agency.city,
            'state': agency.state,
            'postalCode': agency.postal_code,
            'isVerified': agency.is_verified,
            'isActive': agency.is_active,
            'documents': {
                'gstDocUrl': agency.gst_doc_url,
                'businessPhotoUrl': agency.business_photo_url
            },
            'createdAt': agency.created_at.isoformat() if agency.created_at else None,
            'updatedAt': agency.updated_at.isoformat() if agency.updated_at else None
        }

    return {
        'profile': {
            'id': profile.id if profile else None,
            'userId': user.id,
            'fullName': profile.full_name if profile and profile.full_name else '',
            'email': user.email,
            'phone': profile.phone if profile and profile.phone else '',
            'avatarUrl': profile.avatar_url if profile else None,
            'avatarLocked': profile.avatar_locked if profile else False,
            'memberSince': user.created_at.isoformat() if user.created_at else None
        },
        'metrics': {
            'vehiclesListed': len(vehicles),
            'completedTrips': len(bookings),
            'loyaltyScore': loyalty_score,
            'nextMilestoneTrips': next_milestone
        },
        'agencyStatus': {
            'hasAgency': agency is not None,
            'agencyId': agency.id if agency else None,
            'agencyName': agency.agency_name if agency else None,
            'isVerified': agency.is_verified if agency else False,
            'canManageFleet': agency is not None,
            'stats': {
                'listedVehicles': (agency.total_vehicles if agency and agency.total_vehicles is not None else len(vehicles)),
                'lifetimeBookings': (agency.total_bookings if agency and agency.total_bookings is not None else len(bookings)),
                'lifetimeEarnings': (agency.total_earnings if agency and agency.total_earnings is not None else 0)
            }
        },
        'agencyDetails': agency_details
    }

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    user_id = get_jwt_identity()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    return jsonify(_build_profile_payload(user, profile)), 200

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.session.add(profile)
    
    profile.full_name = data.get('fullName', profile.full_name)
    profile.phone = data.get('phone', profile.phone)

    new_avatar = data.get('avatarUrl')
    if new_avatar is not None and not profile.avatar_locked:
        profile.avatar_url = new_avatar
    
    db.session.commit()
    
    payload = _build_profile_payload(user, profile)
    payload['message'] = 'Profile updated successfully'
    return jsonify(payload), 200

@users_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID (public)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    return jsonify({
        'user': {
            'id': user.id,
            'email': user.email,
            'profile': {
                'fullName': profile.full_name if profile else '',
                'phone': profile.phone if profile else '',
                'avatarUrl': profile.avatar_url if profile else None
            }
        }
    }), 200
