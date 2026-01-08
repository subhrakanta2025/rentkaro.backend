from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from app.models.agency import Agency
from app.models.user import User, Profile
from app.models.booking import Booking
from app.models.vehicle import Vehicle
from datetime import datetime, timedelta
import os
import uuid

agencies_bp = Blueprint('agencies', __name__, url_prefix='/api/agencies')

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    base_upload = current_app.config.get('UPLOAD_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads'))
    agency_folder = os.path.join(base_upload, 'agencies')
    os.makedirs(agency_folder, exist_ok=True)
    return agency_folder

@agencies_bp.route('', methods=['GET'])
def get_agencies():
    """Get all agencies"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    city = request.args.get('city')
    
    query = Agency.query.filter_by(is_verified=True, is_active=True)
    
    if city:
        query = query.filter(Agency.city.ilike(f'%{city}%'))
    
    agencies = query.paginate(page=page, per_page=per_page)
    
    result = []
    for agency in agencies.items:
        user = User.query.get(agency.user_id)
        result.append({
            'id': agency.id,
            'agencyName': agency.agency_name,
            'city': agency.city,
            'state': agency.state,
            'phoneNumber': agency.agency_phone,
            'totalVehicles': agency.total_vehicles,
            'totalBookings': agency.total_bookings,
            'totalEarnings': agency.total_earnings,
            'averageRating': agency.average_rating,
            'isVerified': agency.is_verified,
            'contactEmail': agency.agency_email
        })
    
    return jsonify({
        'agencies': result,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': agencies.total,
            'pages': agencies.pages
        }
    }), 200


@agencies_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_agency():
    """Return the agency record for the authenticated user."""
    user_id = get_jwt_identity()
    agency = Agency.query.filter_by(user_id=user_id).first()
    if not agency:
        return jsonify({'agency': None}), 200

    user = User.query.get(agency.user_id)

    return jsonify({
        'agency': {
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
            'latitude': agency.latitude,
            'longitude': agency.longitude,
            'isVerified': agency.is_verified,
            'isActive': agency.is_active,
            'totalVehicles': agency.total_vehicles,
            'totalBookings': agency.total_bookings,
            'totalEarnings': agency.total_earnings,
            'averageRating': agency.average_rating,
            'contact': {
                'userId': user.id if user else None,
                'email': user.email if user else None,
                'name': user.profile.full_name if user and user.profile else ''
            }
        }
    }), 200


@agencies_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_my_agency():
    """Update the agency profile for the authenticated user."""
    user_id = get_jwt_identity()
    
    agency = Agency.query.filter_by(user_id=user_id).first()
    if not agency:
        return jsonify({'error': 'Agency not found'}), 404
    
    is_multipart = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form if is_multipart else request.get_json() or {}
    
    try:
        # Update basic fields
        if 'agencyName' in data:
            agency.agency_name = data['agencyName']
        if 'businessType' in data:
            agency.business_type = data['businessType']
        if 'registrationNumber' in data:
            agency.registration_number = data['registrationNumber']
        if 'gstNumber' in data:
            agency.gst_number = data['gstNumber']
        if 'panNumber' in data:
            agency.pan_number = data['panNumber']
        if 'agencyPhone' in data:
            agency.agency_phone = data['agencyPhone']
        if 'agencyEmail' in data:
            agency.agency_email = data['agencyEmail'].lower().strip() if data['agencyEmail'] else None
        if 'address' in data:
            agency.address = data['address']
        if 'city' in data:
            agency.city = data['city']
        if 'state' in data:
            agency.state = data['state']
        if 'postalCode' in data:
            agency.postal_code = data['postalCode']
        if 'latitude' in data:
            agency.latitude = data['latitude']
        if 'longitude' in data:
            agency.longitude = data['longitude']
        
        # Handle file uploads if multipart
        if is_multipart:
            upload_folder = get_upload_folder()
            
            gst_doc = request.files.get('gstDoc')
            if gst_doc and gst_doc.filename:
                if not allowed_file(gst_doc.filename):
                    return jsonify({'error': 'Invalid file type for gstDoc'}), 400
                ext = gst_doc.filename.rsplit('.', 1)[1].lower()
                filename = f"{user_id}_gstDoc_{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(upload_folder, secure_filename(filename))
                gst_doc.save(filepath)
                agency.gst_doc_url = f"/uploads/agencies/{filename}"
            
            business_photo = request.files.get('businessPhoto')
            if business_photo and business_photo.filename:
                if not allowed_file(business_photo.filename):
                    return jsonify({'error': 'Invalid file type for businessPhoto'}), 400
                ext = business_photo.filename.rsplit('.', 1)[1].lower()
                filename = f"{user_id}_businessPhoto_{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(upload_folder, secure_filename(filename))
                business_photo.save(filepath)
                agency.business_photo_url = f"/uploads/agencies/{filename}"
        
        # Handle bank details if provided
        bank_data = data.get('bankDetails')
        if bank_data and isinstance(bank_data, dict):
            if 'accountNumber' in bank_data:
                agency.bank_account_number = bank_data['accountNumber']
            if 'ifscCode' in bank_data:
                agency.bank_ifsc_code = bank_data['ifscCode']
            if 'accountHolderName' in bank_data:
                agency.bank_account_holder_name = bank_data['accountHolderName']
        
        db.session.commit()
        
        return jsonify({'message': 'Agency profile updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@agencies_bp.route('/<agency_id>', methods=['GET'])
def get_agency(agency_id):
    """Get agency details"""
    agency = Agency.query.get(agency_id)
    
    if not agency:
        return jsonify({'error': 'Agency not found'}), 404
    
    user = User.query.get(agency.user_id)
    
    return jsonify({
        'agency': {
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
            'latitude': agency.latitude,
            'longitude': agency.longitude,
            'isVerified': agency.is_verified,
            'isActive': agency.is_active,
            'totalVehicles': agency.total_vehicles,
            'totalBookings': agency.total_bookings,
            'totalEarnings': agency.total_earnings,
            'averageRating': agency.average_rating,
            'contact': {
                'userId': user.id,
                'email': user.email,
                'name': user.profile.full_name if user.profile else ''
            }
        }
    }), 200

@agencies_bp.route('', methods=['POST'])
@jwt_required()
def create_agency():
    """Create agency with optional documents"""
    user_id = get_jwt_identity()

    if Agency.query.filter_by(user_id=user_id).first():
        return jsonify({'error': 'User already has an agency'}), 409

    is_multipart = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form if is_multipart else request.get_json() or {}

    try:
        agency_email = data.get('agencyEmail')
        if agency_email:
            agency_email = agency_email.lower().strip()

        upload_folder = get_upload_folder()
        gst_doc_url = None
        business_photo_url = None

        if is_multipart:
            for field, target in [('gstDoc', 'gst_doc_url'), ('businessPhoto', 'business_photo_url')]:
                file = request.files.get(field)
                if file and file.filename:
                    if not allowed_file(file.filename):
                        return jsonify({'error': f'Invalid file type for {field}'}), 400
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"{user_id}_{field}_{uuid.uuid4().hex}.{ext}"
                    filepath = os.path.join(upload_folder, secure_filename(filename))
                    file.save(filepath)
                    url = f"/uploads/agencies/{filename}"
                    if target == 'gst_doc_url':
                        gst_doc_url = url
                    else:
                        business_photo_url = url

        agency = Agency(
            user_id=user_id,
            agency_name=data.get('agencyName'),
            business_type=data.get('businessType'),
            registration_number=data.get('registrationNumber'),
            gst_number=data.get('gstNumber'),
            pan_number=data.get('panNumber'),
            agency_phone=data.get('agencyPhone'),
            agency_email=agency_email,
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            postal_code=data.get('postalCode'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            gst_doc_url=gst_doc_url,
            business_photo_url=business_photo_url
        )

        db.session.add(agency)
        db.session.commit()

        return jsonify({
            'message': 'Agency created successfully',
            'agency': {'id': agency.id}
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@agencies_bp.route('/<agency_id>', methods=['PUT'])
@jwt_required()
def update_agency(agency_id):
    """Update agency"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    agency = Agency.query.get(agency_id)
    if not agency:
        return jsonify({'error': 'Agency not found'}), 404
    
    if agency.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        agency.agency_name = data.get('agencyName', agency.agency_name)
        agency.business_type = data.get('businessType', agency.business_type)
        agency.registration_number = data.get('registrationNumber', agency.registration_number)
        agency.gst_number = data.get('gstNumber', agency.gst_number)
        agency.pan_number = data.get('panNumber', agency.pan_number)
        agency.agency_phone = data.get('agencyPhone', agency.agency_phone)
        
        # Normalize agency email to lowercase
        agency_email = data.get('agencyEmail')
        if agency_email:
            agency_email = agency_email.lower().strip()
            agency.agency_email = agency_email
        else:
            agency.agency_email = data.get('agencyEmail', agency.agency_email)
        agency.address = data.get('address', agency.address)
        agency.city = data.get('city', agency.city)
        agency.state = data.get('state', agency.state)
        agency.postal_code = data.get('postalCode', agency.postal_code)
        agency.latitude = data.get('latitude', agency.latitude)
        agency.longitude = data.get('longitude', agency.longitude)
        
        bank_data = data.get('bankDetails', {})
        if bank_data:
            agency.bank_account_number = bank_data.get('accountNumber', agency.bank_account_number)
            agency.bank_ifsc_code = bank_data.get('ifscCode', agency.bank_ifsc_code)
            agency.bank_account_holder_name = bank_data.get('accountHolderName', agency.bank_account_holder_name)
        
        db.session.commit()
        
        return jsonify({'message': 'Agency updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def _get_range_dates(range_key: str, now: datetime):
    """Return (current_start, previous_start, previous_end) for the given range key."""
    range_key = (range_key or 'month').lower()
    if range_key == 'week':
        current_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)
        previous_end = current_start
    elif range_key == 'year':
        current_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_start = current_start.replace(year=current_start.year - 1)
        previous_end = current_start
    else:  # default month
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Move to previous month start
        prev_month = current_start.month - 1 or 12
        prev_year = current_start.year if current_start.month > 1 else current_start.year - 1
        previous_start = current_start.replace(year=prev_year, month=prev_month)
        previous_end = current_start
    return current_start, previous_start, previous_end


def _month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    return dt.replace(year=year, month=month, day=1)


@agencies_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_agency_earnings():
    """Return earnings and analytics for the authenticated agency owner."""
    user_id = get_jwt_identity()
    agency = Agency.query.filter_by(user_id=user_id).first()
    if not agency:
        return jsonify({'error': 'Agency not found for user'}), 404

    range_key = request.args.get('range', 'month').lower()
    now = datetime.utcnow()
    current_start, previous_start, previous_end = _get_range_dates(range_key, now)

    # Base query: completed payments for this agency
    base_query = Booking.query.filter_by(agency_id=agency.id, payment_status='completed')

    current_bookings = base_query.filter(Booking.start_date >= current_start).all()
    previous_bookings = base_query.filter(
        Booking.start_date >= previous_start,
        Booking.start_date < previous_end
    ).all()

    # Load vehicle metadata for current bookings
    vehicle_ids = list({b.vehicle_id for b in current_bookings})
    vehicles_map = {}
    if vehicle_ids:
        vehicles = Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all()
        vehicles_map = {v.id: v for v in vehicles}

    def _safe_amount(booking: Booking) -> float:
        return float(booking.total_amount or 0)

    total_earnings = sum(_safe_amount(b) for b in current_bookings)
    total_bookings = len(current_bookings)
    average_per_booking = total_earnings / total_bookings if total_bookings else 0

    previous_earnings = sum(_safe_amount(b) for b in previous_bookings)
    if previous_earnings:
        growth_rate = ((total_earnings - previous_earnings) / previous_earnings) * 100
    else:
        growth_rate = 100.0 if total_earnings > 0 else 0.0

    # Earnings by vehicle type and vehicle performance
    type_earnings = {}
    vehicle_stats = {}
    for booking in current_bookings:
        vehicle = vehicles_map.get(booking.vehicle_id)
        v_type = (vehicle.vehicle_type if vehicle and vehicle.vehicle_type else 'other').lower()
        name = f"{vehicle.make} {vehicle.model}" if vehicle else 'Unknown Vehicle'

        type_earnings[v_type] = type_earnings.get(v_type, 0) + _safe_amount(booking)

        if booking.vehicle_id not in vehicle_stats:
            vehicle_stats[booking.vehicle_id] = {
                'name': name,
                'type': v_type,
                'bookings': 0,
                'earnings': 0.0,
            }
        vehicle_stats[booking.vehicle_id]['bookings'] += 1
        vehicle_stats[booking.vehicle_id]['earnings'] += _safe_amount(booking)

    top_vehicle = None
    if vehicle_stats:
        top_id = max(vehicle_stats, key=lambda vid: vehicle_stats[vid]['earnings'])
        top_data = vehicle_stats[top_id]
        top_vehicle = {
          'name': top_data['name'],
          'type': top_data['type'],
          'bookings': top_data['bookings'],
          'earnings': round(top_data['earnings'], 2),
          'avgPerBooking': round(top_data['earnings'] / top_data['bookings'], 2) if top_data['bookings'] else 0,
        }

    # Monthly trend for last 6 months (including current), using all completed bookings
    all_completed_bookings = base_query.all()
    current_month_start = _month_start(now)
    monthly_trend = []
    for offset in range(5, -1, -1):
        start = _add_months(current_month_start, -offset)
        end = _add_months(start, 1)
        month_earnings = 0.0
        month_bookings = 0
        for booking in all_completed_bookings:
            if booking.start_date >= start and booking.start_date < end:
                month_earnings += _safe_amount(booking)
                month_bookings += 1
        monthly_trend.append({
            'month': start.strftime('%b'),
            'earnings': round(month_earnings, 2),
            'bookings': month_bookings
        })

    # Build category distribution (2W/4W/Other)
    total_for_share = total_earnings or 1  # avoid division by zero
    categories = []
    two_w = type_earnings.get('bike', 0) + type_earnings.get('scooter', 0)
    four_w = type_earnings.get('car', 0)
    other_w = total_earnings - two_w - four_w
    for name, amount, key in [
        ('2 Wheelers', two_w, 'bike'),
        ('4 Wheelers', four_w, 'car'),
        ('Other', other_w, 'other'),
    ]:
        categories.append({
            'name': name,
            'type': key,
            'earnings': round(amount, 2),
            'percentage': round((amount / total_for_share) * 100, 1) if total_for_share else 0
        })

    vehicle_performance = [
        {
            'name': stats['name'],
            'type': stats['type'],
            'bookings': stats['bookings'],
            'earnings': round(stats['earnings'], 2),
            'avgPerBooking': round(stats['earnings'] / stats['bookings'], 2) if stats['bookings'] else 0
        }
        for stats in vehicle_stats.values()
    ]
    vehicle_performance.sort(key=lambda v: v['earnings'], reverse=True)

    # Payment methods are not tracked in schema; return empty list for now
    payment_methods = []

    return jsonify({
        'range': range_key,
        'summary': {
            'totalEarnings': round(total_earnings, 2),
            'totalBookings': total_bookings,
            'averagePerBooking': round(average_per_booking, 2),
            'growthRate': round(growth_rate, 1),
            'topVehicle': top_vehicle
        },
        'categories': categories,
        'monthlyTrend': monthly_trend,
        'vehiclePerformance': vehicle_performance,
        'paymentMethods': payment_methods
    }), 200
