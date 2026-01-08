from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app import db
from app.models.vehicle import Vehicle, VehicleImage, VehicleDocument
from app.models.user import User
from app.models.agency import Agency
from app.models.booking import Booking
from app.models.favorite import Favorite
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_

vehicles_bp = Blueprint('vehicles', __name__, url_prefix='/api/vehicles')


def _absolute_url(path: str) -> str:
    """Return absolute URL for stored file paths that start with /uploads."""
    if not path:
        return path
    if path.startswith('http://') or path.startswith('https://'):
        return path
    if path.startswith('/'):
        base = request.host_url.rstrip('/')
        return f"{base}{path}"
    return path


def _parse_iso_date(value, field_name: str):
    """Parse ISO-8601 date/datetime strings to date objects."""
    if value is None or value == '':
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '')).date()
        except ValueError:
            raise ValueError(f"{field_name} must be a valid ISO-8601 date (YYYY-MM-DD)")
    raise ValueError(f"{field_name} must be a valid date string")

@vehicles_bp.route('', methods=['GET'])
def get_vehicles():
    """Get all available vehicles"""
    print('[BACKEND] GET /api/vehicles called')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    vehicle_type = request.args.get('type')
    wheelers = request.args.get('wheelers')  # expected: 2, 4, two, four, 2w, 4w
    search_term = request.args.get('q')
    location = request.args.get('location')
    favorite_only = request.args.get('favorite')
    start_date = request.args.get('start_date') or request.args.get('startDate')
    end_date = request.args.get('end_date') or request.args.get('endDate')
    pickup_date = request.args.get('pickup_date')
    pickup_time = request.args.get('pickup_time')
    drop_date = request.args.get('drop_date')
    drop_time = request.args.get('drop_time')
    
    print(f'[BACKEND] Params: page={page}, per_page={per_page}, type={vehicle_type}, wheelers={wheelers}, q={search_term}, location={location}, favorite={favorite_only}')

    current_user_id = None
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
    except Exception:
        current_user_id = None
    
    query = Vehicle.query.filter_by(is_available=True)

    # Optional availability window: exclude vehicles that have overlapping bookings
    if (pickup_date and drop_date) or (start_date and end_date):
        try:
            if pickup_date and drop_date:
                if not (pickup_time and drop_time):
                    return jsonify({'error': 'pickup_date/drop_date require pickup_time and drop_time'}), 400
                start_dt = datetime.fromisoformat(f"{pickup_date}T{pickup_time}")
                end_dt = datetime.fromisoformat(f"{drop_date}T{drop_time}")
            else:
                start_dt = datetime.fromisoformat(start_date.replace('Z', ''))
                end_dt = datetime.fromisoformat(end_date.replace('Z', ''))
        except ValueError:
            return jsonify({'error': 'Invalid date format; use ISO-8601 for start_date/end_date or YYYY-MM-DD with HH:MM for pickup/drop'}), 400

        if end_dt <= start_dt:
            return jsonify({'error': 'end_date/drop_time must be after start_date/pickup_time'}), 400

        cutoff = datetime.utcnow() - timedelta(minutes=2)
        blocking_statuses = ['confirmed', 'active']
        overlapping = Booking.query.filter(
            or_(
                Booking.status.in_(blocking_statuses),
                and_(Booking.status == 'pending', Booking.created_at >= cutoff)
            ),
            Booking.start_date < end_dt,
            Booking.end_date > start_dt
        ).with_entities(Booking.vehicle_id).distinct()
        query = query.filter(~Vehicle.id.in_(overlapping))

    # Wheelers filter maps to vehicle_type buckets
    if wheelers:
        wheelers_lower = wheelers.strip().lower()
        two_wheeler_types = ['bike', 'scooter', 'motorcycle']
        four_wheeler_types = ['car', 'suv', 'sedan', 'hatchback']
        if wheelers_lower in ['2', '2w', 'two', 'two-wheeler', '2-wheeler', '2 wheeler']:
            query = query.filter(Vehicle.vehicle_type.in_(two_wheeler_types))
        elif wheelers_lower in ['4', '4w', 'four', 'four-wheeler', '4-wheeler', '4 wheeler']:
            query = query.filter(Vehicle.vehicle_type.in_(four_wheeler_types))

    if favorite_only:
        if not current_user_id:
            return jsonify({'error': 'Authentication required for favorite filter'}), 401
        favorite_subquery = Favorite.query.filter_by(user_id=current_user_id).with_entities(Favorite.vehicle_id)
        query = query.filter(Vehicle.id.in_(favorite_subquery))

    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)

    if location:
        query = query.filter(Vehicle.location.ilike(f'%{location}%'))

    if search_term:
        like_term = f"%{search_term}%"
        query = query.filter(
            or_(
                Vehicle.make.ilike(like_term),
                Vehicle.model.ilike(like_term),
                Vehicle.location.ilike(like_term)
            )
        )

    order_column = getattr(Vehicle, 'created_at', Vehicle.id)
    vehicles = query.order_by(order_column.desc()).paginate(page=page, per_page=per_page)
    favorite_ids = set()
    if current_user_id and vehicles.items:
        favs = Favorite.query.filter(
            Favorite.user_id == current_user_id,
            Favorite.vehicle_id.in_([v.id for v in vehicles.items])
        ).all()
        favorite_ids = {f.vehicle_id for f in favs}
    print(f'[BACKEND] Found {len(vehicles.items)} vehicles')
    
    result = []
    for vehicle in vehicles.items:
        images = VehicleImage.query.filter_by(vehicle_id=vehicle.id).all()
        primary_image = None
        if images:
            primary_image = next((img for img in images if img.is_primary), images[0])

        agency_name = None
        agency_logo = None
        if vehicle.agency_id:
            agency = Agency.query.get(vehicle.agency_id)
            # Agency model stores the field as agency_name
            agency_name = agency.agency_name if agency else None
            # Use business photo as logo placeholder when available
            agency_logo = getattr(agency, 'business_photo_url', None) if agency else None
        
        result.append({
            'id': vehicle.id,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'agencyId': vehicle.agency_id,
            'agencyName': agency_name,
            'agencyLogo': _absolute_url(agency_logo) if agency_logo else None,
            'vehicleType': vehicle.vehicle_type,
            'fuelType': vehicle.fuel_type,
            'color': vehicle.color,
            'dailyRate': vehicle.daily_rate,
            'weeklyRate': vehicle.weekly_rate,
            'monthlyRate': vehicle.monthly_rate,
            'location': vehicle.location,
            'imageUrl': _absolute_url(primary_image.image_url) if primary_image else None,
            'seatingCapacity': vehicle.seating_capacity,
            'transmission': vehicle.transmission,
            'isAvailable': vehicle.is_available,
            'status': vehicle.status,
            'mileage': vehicle.mileage,
            'securityDeposit': vehicle.security_deposit,
            'displacement': vehicle.displacement,
            'topSpeed': vehicle.top_speed,
            'fuelCapacity': vehicle.fuel_capacity,
            'weight': vehicle.weight,
            'lateFeePerHr': vehicle.late_fee_per_hr,
            'excessPerKm': vehicle.excess_per_km,
            'timings': vehicle.timings,
            'isFavorite': vehicle.id in favorite_ids,
        })
    
    print(f'[BACKEND] Returning {len(result)} vehicles')
    return jsonify({
        'vehicles': result,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': vehicles.total,
            'pages': vehicles.pages
        }
    }), 200

@vehicles_bp.route('/<vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    """Get vehicle details"""
    vehicle = Vehicle.query.get(vehicle_id)
    
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    images = VehicleImage.query.filter_by(vehicle_id=vehicle_id).all()
    documents = VehicleDocument.query.filter_by(vehicle_id=vehicle_id).all()
    
    owner = User.query.get(vehicle.owner_id)
    owner_profile = owner.profile if owner else None

    agency = Agency.query.get(vehicle.agency_id) if vehicle.agency_id else None

    
    return jsonify({
        'vehicle': {
            'id': vehicle.id,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'agencyId': vehicle.agency_id,
            'registrationNumber': vehicle.registration_number,
            'vin': vehicle.vin,
            'vehicleType': vehicle.vehicle_type,
            'fuelType': vehicle.fuel_type,
            'color': vehicle.color,
            'mileage': vehicle.mileage,
            'seatingCapacity': vehicle.seating_capacity,
            'transmission': vehicle.transmission,
            'dailyRate': vehicle.daily_rate,
            'weeklyRate': vehicle.weekly_rate,
            'monthlyRate': vehicle.monthly_rate,
            'securityDeposit': vehicle.security_deposit,
            'displacement': vehicle.displacement,
            'topSpeed': vehicle.top_speed,
            'fuelCapacity': vehicle.fuel_capacity,
            'weight': vehicle.weight,
            'lateFeePerHr': vehicle.late_fee_per_hr,
            'excessPerKm': vehicle.excess_per_km,
            'timings': vehicle.timings,
            'isAvailable': vehicle.is_available,
            'status': vehicle.status,
            'location': vehicle.location,
            'latitude': vehicle.latitude,
            'longitude': vehicle.longitude,
            'insuranceNumber': vehicle.insurance_number,
            'insuranceExpiry': vehicle.insurance_expiry.isoformat() if vehicle.insurance_expiry else None,
            'registrationExpiry': vehicle.registration_expiry.isoformat() if vehicle.registration_expiry else None,
            'pollutionCertificateNumber': vehicle.pollution_certificate_number,
            'pollutionExpiry': vehicle.pollution_expiry.isoformat() if vehicle.pollution_expiry else None,
            'images': [{
                'id': img.id,
                'imageUrl': _absolute_url(img.image_url),
                'imageType': img.image_type,
                'isPrimary': img.is_primary
            } for img in images],
            'documents': [{
                'id': doc.id,
                'documentType': doc.document_type,
                'documentUrl': _absolute_url(doc.document_url),
                'expiryDate': doc.expiry_date.isoformat() if doc.expiry_date else None,
                'verified': doc.verified
            } for doc in documents],
            'owner': {
                'id': owner.id,
                'name': owner_profile.full_name if owner_profile else '',
                'phone': owner_profile.phone if owner_profile else ''
            },
            'agency': {
                'id': agency.id if agency else None,
                'name': agency.agency_name if agency else None,
                'address': agency.address if agency else None,
                'city': agency.city if agency else None,
                'state': agency.state if agency else None,
                'latitude': agency.latitude if agency else None,
                'longitude': agency.longitude if agency else None,
                'phone': agency.agency_phone if agency else None,
            } if agency else None
        }
    }), 200

@vehicles_bp.route('', methods=['POST'])
@jwt_required()
def create_vehicle():
    """Create a new vehicle"""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    
    try:
        insurance_expiry = _parse_iso_date(data.get('insuranceExpiry'), 'insuranceExpiry')
        registration_expiry = _parse_iso_date(data.get('registrationExpiry'), 'registrationExpiry')
        pollution_expiry = _parse_iso_date(data.get('pollutionExpiry'), 'pollutionExpiry')

        vehicle = Vehicle(
            owner_id=user_id,
            agency_id=data.get('agencyId') or data.get('agency_id'),
            make=data.get('brand') or data['make'],
            model=data.get('modelName') or data['model'],
            year=data['year'],
            registration_number=data['registrationNumber'],
            vin=data.get('vin'),
            vehicle_type=data['vehicleType'],
            fuel_type=data['fuelType'],
            transmission=data.get('transmission'),
            color=data.get('color'),
            mileage=data.get('mileage'),
            seating_capacity=data.get('seatingCapacity'),
            displacement=data.get('displacement'),
            top_speed=data.get('topSpeed'),
            fuel_capacity=data.get('fuelCapacity'),
            weight=data.get('weight'),
            late_fee_per_hr=data.get('lateFeePerHr'),
            excess_per_km=data.get('excessPerKm'),
            timings=data.get('timings'),
            daily_rate=data.get('price_per_day') or data.get('dailyRate') or data['dailyRate'],
            weekly_rate=data.get('weeklyRate'),
            monthly_rate=data.get('monthlyRate'),
            security_deposit=data.get('securityDeposit', 0),
            location=data.get('location'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            insurance_number=data.get('insuranceNumber'),
            insurance_expiry=insurance_expiry,
            registration_expiry=registration_expiry,
            pollution_certificate_number=data.get('pollutionCertificateNumber'),
            pollution_expiry=pollution_expiry
        )
        
        db.session.add(vehicle)
        db.session.flush()
        
        # Add images
        images = data.get('images', [])
        for idx, image in enumerate(images):
            vehicle_image = VehicleImage(
                vehicle_id=vehicle.id,
                image_url=image['imageUrl'],
                image_type=image.get('imageType'),
                is_primary=image.get('isPrimary', idx == 0)
            )
            db.session.add(vehicle_image)
        
        # Add documents
        documents = data.get('documents', [])
        for doc in documents:
            vehicle_doc = VehicleDocument(
                vehicle_id=vehicle.id,
                document_type=doc['documentType'],
                document_url=doc['documentUrl'],
                expiry_date=_parse_iso_date(doc.get('expiryDate'), 'documents.expiryDate'),
                verified=doc.get('verified', False)
            )
            db.session.add(vehicle_doc)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vehicle created successfully',
            'vehicle': {'id': vehicle.id}
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@vehicles_bp.route('/<vehicle_id>', methods=['PUT'])
@jwt_required()
def update_vehicle(vehicle_id):
    """Update vehicle"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    if vehicle.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        insurance_expiry = _parse_iso_date(data.get('insuranceExpiry', vehicle.insurance_expiry), 'insuranceExpiry')
        registration_expiry = _parse_iso_date(data.get('registrationExpiry', vehicle.registration_expiry), 'registrationExpiry')
        pollution_expiry = _parse_iso_date(data.get('pollutionExpiry', vehicle.pollution_expiry), 'pollutionExpiry')

        vehicle.make = data.get('brand', data.get('make', vehicle.make))
        vehicle.model = data.get('modelName', data.get('model', vehicle.model))
        vehicle.year = data.get('year', vehicle.year)
        vehicle.vehicle_type = data.get('vehicleType', vehicle.vehicle_type)
        vehicle.fuel_type = data.get('fuelType', vehicle.fuel_type)
        vehicle.color = data.get('color', vehicle.color)
        vehicle.mileage = data.get('mileage', vehicle.mileage)
        vehicle.seating_capacity = data.get('seatingCapacity', vehicle.seating_capacity)
        vehicle.displacement = data.get('displacement', vehicle.displacement)
        vehicle.top_speed = data.get('topSpeed', vehicle.top_speed)
        vehicle.fuel_capacity = data.get('fuelCapacity', vehicle.fuel_capacity)
        vehicle.weight = data.get('weight', vehicle.weight)
        vehicle.late_fee_per_hr = data.get('lateFeePerHr', vehicle.late_fee_per_hr)
        vehicle.excess_per_km = data.get('excessPerKm', vehicle.excess_per_km)
        vehicle.timings = data.get('timings', vehicle.timings)
        vehicle.transmission = data.get('transmission', vehicle.transmission)
        vehicle.daily_rate = data.get('price_per_day', data.get('dailyRate', vehicle.daily_rate))
        vehicle.weekly_rate = data.get('weeklyRate', vehicle.weekly_rate)
        vehicle.monthly_rate = data.get('monthlyRate', vehicle.monthly_rate)
        vehicle.security_deposit = data.get('securityDeposit', vehicle.security_deposit)
        vehicle.location = data.get('location', vehicle.location)
        vehicle.latitude = data.get('latitude', vehicle.latitude)
        vehicle.longitude = data.get('longitude', vehicle.longitude)
        agency_id = data.get('agencyId') or data.get('agency_id')
        if agency_id:
            vehicle.agency_id = agency_id
        vehicle.insurance_number = data.get('insuranceNumber', vehicle.insurance_number)
        vehicle.insurance_expiry = insurance_expiry
        vehicle.registration_expiry = registration_expiry
        vehicle.pollution_certificate_number = data.get('pollutionCertificateNumber', vehicle.pollution_certificate_number)
        vehicle.pollution_expiry = pollution_expiry
        
        # Replace images when provided
        if 'images' in data:
            VehicleImage.query.filter_by(vehicle_id=vehicle.id).delete()
            images = data.get('images', []) or []
            for idx, image in enumerate(images):
                vehicle_image = VehicleImage(
                    vehicle_id=vehicle.id,
                    image_url=image.get('imageUrl'),
                    image_type=image.get('imageType'),
                    is_primary=image.get('isPrimary', idx == 0)
                )
                db.session.add(vehicle_image)

        # Replace documents when provided
        if 'documents' in data:
            VehicleDocument.query.filter_by(vehicle_id=vehicle.id).delete()
            documents = data.get('documents', []) or []
            for doc in documents:
                vehicle_doc = VehicleDocument(
                    vehicle_id=vehicle.id,
                    document_type=doc.get('documentType'),
                    document_url=doc.get('documentUrl'),
                    expiry_date=_parse_iso_date(doc.get('expiryDate'), 'documents.expiryDate'),
                    verified=doc.get('verified', False)
                )
                db.session.add(vehicle_doc)

        db.session.commit()
        
        return jsonify({'message': 'Vehicle updated successfully'}), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@vehicles_bp.route('/<vehicle_id>/availability', methods=['PUT'])
@jwt_required()
def update_availability(vehicle_id):
    """Update vehicle availability"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    if vehicle.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    # Safely parse boolean values coming from clients (they may send strings)
    def _to_bool(val, default):
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            v = val.strip().lower()
            if v in ('true', '1', 'yes', 'y', 'on'):
                return True
            if v in ('false', '0', 'no', 'n', 'off'):
                return False
        return default

    try:
        new_avail = _to_bool(data.get('isAvailable'), vehicle.is_available)
        vehicle.is_available = new_avail
        db.session.commit()
        return jsonify({'message': 'Availability updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'[ERROR] update_availability failed for vehicle {vehicle_id}:', e)
        return jsonify({'error': str(e)}), 500

@vehicles_bp.route('/<vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    """Delete vehicle"""
    user_id = get_jwt_identity()
    
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    if vehicle.owner_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(vehicle)
    db.session.commit()
    
    return jsonify({'message': 'Vehicle deleted successfully'}), 200


@vehicles_bp.route('/<vehicle_id>/favorite', methods=['POST'])
@jwt_required()
def add_favorite(vehicle_id):
    """Mark a vehicle as favorite for the current user"""
    user_id = get_jwt_identity()
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    existing = Favorite.query.filter_by(user_id=user_id, vehicle_id=vehicle_id).first()
    if existing:
        return jsonify({'message': 'Already favorited'}), 200

    fav = Favorite(user_id=user_id, vehicle_id=vehicle_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({'message': 'Added to favorites'}), 201


@vehicles_bp.route('/<vehicle_id>/favorite', methods=['DELETE'])
@jwt_required()
def remove_favorite(vehicle_id):
    """Remove vehicle from favorites for the current user"""
    user_id = get_jwt_identity()
    deleted = Favorite.query.filter_by(user_id=user_id, vehicle_id=vehicle_id).delete()
    if deleted:
        db.session.commit()
        return jsonify({'message': 'Removed from favorites'}), 200
    return jsonify({'message': 'Favorite not found'}), 404

@vehicles_bp.route('/owner/<owner_id>', methods=['GET'])
def get_owner_vehicles(owner_id):
    """Get all vehicles of an owner"""
    vehicles = Vehicle.query.filter_by(owner_id=owner_id).all()

    result = []
    for vehicle in vehicles:
        images = VehicleImage.query.filter_by(vehicle_id=vehicle.id).all()
        primary_image = None
        if images:
            primary_image = next((img for img in images if img.is_primary), images[0])

        result.append({
            'id': vehicle.id,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'vehicleType': vehicle.vehicle_type,
            'fuelType': vehicle.fuel_type,
            'dailyRate': vehicle.daily_rate,
            'isAvailable': vehicle.is_available,
            'status': vehicle.status,
            'imageUrl': _absolute_url(primary_image.image_url) if primary_image else None
        })

    return jsonify({'vehicles': result}), 200
