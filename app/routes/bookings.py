from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.booking import Booking
from app.models.vehicle import Vehicle, VehicleImage
from app.models.agency import Agency
from app.models.user import User
from app.models.payment import Payment
from sqlalchemy import or_
from datetime import datetime
import os
import requests
import hmac
import hashlib
import json

bookings_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')

# Razorpay configuration (defaults to provided test keys; override via env vars)
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_Id1p2FvmwenNvx')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '3rlD8oSZROnayZdojYvkKtHO')


def _create_razorpay_order(amount_paise: int, receipt: str, notes: dict | None = None):
    payload = {
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': receipt,
        'payment_capture': 1,
        'notes': notes or {},
    }
    # Razorpay expects JSON so nested objects like notes remain a map
    response = requests.post(
        'https://api.razorpay.com/v1/orders',
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
        json=payload,
    )
    if response.status_code >= 300:
        raise Exception(response.text)
    return response.json()


def _verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    message = f"{order_id}|{payment_id}".encode()
    generated = hmac.new(RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(generated, signature)

@bookings_bp.route('', methods=['GET'])
@jwt_required()
def get_bookings():
    """Get bookings for authenticated user/agency with optional filters."""
    user_id = get_jwt_identity()
    status = request.args.get('status')
    vehicle_type = request.args.get('vehicle_type')
    search = request.args.get('q')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', type=int)

    agency = Agency.query.filter_by(user_id=user_id).first()
    agency_id = agency.id if agency else None

    if agency_id:
        query = Booking.query.filter(
            or_(
                Booking.customer_id == user_id,
                Booking.agency_id == agency_id
            )
        )
    else:
        query = Booking.query.filter_by(customer_id=user_id)
    
    if status:
        query = query.filter_by(status=status)

    # Join Vehicle for type/search filters
    if vehicle_type or search:
        query = query.join(Vehicle, Booking.vehicle_id == Vehicle.id)

    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type == vehicle_type)

    if search:
        like_term = f"%{search}%"
        # Join User for search on email/phone if not already
        query = query.join(User, Booking.customer_id == User.id)
        query = query.filter(
            or_(
                Booking.id.ilike(like_term),
                Vehicle.make.ilike(like_term),
                Vehicle.model.ilike(like_term),
                Booking.pickup_location.ilike(like_term),
                Booking.dropoff_location.ilike(like_term),
                User.email.ilike(like_term),
            )
        )

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Booking.start_date >= start_dt)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format; use ISO-8601'}), 400

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Booking.start_date <= end_dt)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format; use ISO-8601'}), 400

    query = query.order_by(Booking.start_date.desc())
    if limit:
        query = query.limit(limit)
    
    bookings = query.all()
    
    result = []
    for booking in bookings:
        vehicle = Vehicle.query.get(booking.vehicle_id)
        vehicle_image = VehicleImage.query.filter_by(
            vehicle_id=booking.vehicle_id,
            is_primary=True
        ).first()
        customer = User.query.get(booking.customer_id)
        customer_profile = customer.profile if customer else None
        result.append({
            'id': booking.id,
            'vehicleId': booking.vehicle_id,
            'vehicleName': f"{vehicle.make} {vehicle.model}" if vehicle else '',
            'vehicleType': vehicle.vehicle_type if vehicle else None,
            'vehicleImage': vehicle_image.image_url if vehicle_image else None,
            'customerId': booking.customer_id,
            'agencyId': booking.agency_id,
            'startDate': booking.start_date.isoformat(),
            'endDate': booking.end_date.isoformat(),
            'pickupLocation': booking.pickup_location,
            'dropoffLocation': booking.dropoff_location,
            'dailyRate': booking.daily_rate,
            'numberOfDays': booking.number_of_days,
            'subtotal': booking.subtotal,
            'tax': booking.tax,
            'discount': booking.discount,
            'totalAmount': booking.total_amount,
            'securityDeposit': booking.security_deposit,
            'status': booking.status,
            'paymentStatus': booking.payment_status,
            'notes': booking.notes,
            'customer': {
                'id': customer.id if customer else None,
                'name': customer_profile.full_name if customer_profile else '',
                'phone': customer_profile.phone if customer_profile else '',
                'email': customer.email if customer else ''
            },
            'createdAt': booking.created_at.isoformat() if booking.created_at else None
        })
    
    return jsonify({'bookings': result}), 200

@bookings_bp.route('/<booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get booking details"""
    user_id = get_jwt_identity()
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    agency = Agency.query.filter_by(user_id=user_id).first()
    agency_id = agency.id if agency else None

    if booking.customer_id != user_id and (agency_id is None or booking.agency_id != agency_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    vehicle = Vehicle.query.get(booking.vehicle_id)
    vehicle_image = VehicleImage.query.filter_by(
        vehicle_id=booking.vehicle_id,
        is_primary=True
    ).first()
    customer = User.query.get(booking.customer_id)
    customer_profile = customer.profile if customer else None
    
    return jsonify({
        'booking': {
            'id': booking.id,
            'vehicleId': booking.vehicle_id,
            'vehicleName': f"{vehicle.make} {vehicle.model}" if vehicle else '',
            'vehicleType': vehicle.vehicle_type if vehicle else None,
            'vehicleImage': vehicle_image.image_url if vehicle_image else None,
            'customerId': booking.customer_id,
            'agencyId': booking.agency_id,
            'startDate': booking.start_date.isoformat(),
            'endDate': booking.end_date.isoformat(),
            'pickupLocation': booking.pickup_location,
            'dropoffLocation': booking.dropoff_location,
            'dailyRate': booking.daily_rate,
            'numberOfDays': booking.number_of_days,
            'subtotal': booking.subtotal,
            'tax': booking.tax,
            'discount': booking.discount,
            'totalAmount': booking.total_amount,
            'securityDeposit': booking.security_deposit,
            'status': booking.status,
            'paymentStatus': booking.payment_status,
            'notes': booking.notes,
            'odometerStart': booking.odometer_start,
            'odometerEnd': booking.odometer_end,
            'customer': {
                'id': customer.id if customer else None,
                'name': customer_profile.full_name if customer_profile else '',
                'phone': customer_profile.phone if customer_profile else '',
                'email': customer.email if customer else ''
            },
            'createdAt': booking.created_at.isoformat() if booking.created_at else None
        }
    }), 200


@bookings_bp.route('/availability', methods=['GET'])
@jwt_required()
def check_vehicle_availability():
    vehicle_id = request.args.get('vehicle_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not vehicle_id or not start_date or not end_date:
        return jsonify({'error': 'vehicle_id, start_date, and end_date are required'}), 400

    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        return jsonify({'error': 'Invalid date format; use ISO-8601'}), 400

    if end_dt <= start_dt:
        return jsonify({'error': 'end_date must be after start_date'}), 400

    overlapping = Booking.query.filter(
        Booking.vehicle_id == vehicle_id,
        Booking.status != 'cancelled',
        Booking.start_date < end_dt,
        Booking.end_date > start_dt
    ).all()

    conflicts = []
    for booking in overlapping:
        conflicts.append({
            'id': booking.id,
            'startDate': booking.start_date.isoformat(),
            'endDate': booking.end_date.isoformat(),
            'status': booking.status,
        })

    return jsonify({
        'vehicleId': vehicle_id,
        'requestedStartDate': start_dt.isoformat(),
        'requestedEndDate': end_dt.isoformat(),
        'isBooked': len(conflicts) > 0,
        'conflicts': conflicts,
    }), 200

@bookings_bp.route('', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new booking for the authenticated customer."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    required_fields = ['vehicleId', 'agencyId', 'startDate', 'endDate', 'pickupLocation', 'dailyRate', 'totalAmount']
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        vehicle = Vehicle.query.get(data['vehicleId'])
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404

        agency = Agency.query.get(data['agencyId'])
        if not agency:
            return jsonify({'error': 'Agency not found'}), 404

        start_dt = datetime.fromisoformat(data['startDate'])
        end_dt = datetime.fromisoformat(data['endDate'])
        if end_dt <= start_dt:
            return jsonify({'error': 'End date must be after start date'}), 400

        # Compute number_of_days if client did not send it
        number_of_days = data.get('numberOfDays')
        if not number_of_days:
            number_of_days = max(1, (end_dt - start_dt).days)

        booking = Booking(
            customer_id=user_id,
            vehicle_id=data['vehicleId'],
            agency_id=data['agencyId'],
            start_date=start_dt,
            end_date=end_dt,
            pickup_location=data['pickupLocation'],
            dropoff_location=data.get('dropoffLocation') or data['pickupLocation'],
            daily_rate=data['dailyRate'],
            number_of_days=number_of_days,
            subtotal=data.get('subtotal', data['totalAmount'] or 0),
            tax=data.get('tax', 0),
            discount=data.get('discount', 0),
            total_amount=data['totalAmount'],
            security_deposit=data.get('securityDeposit', 0),
            notes=data.get('notes'),
            status=data.get('status', 'pending'),
            payment_status=data.get('paymentStatus', 'pending')
        )

        db.session.add(booking)
        db.session.commit()

        return jsonify({
            'message': 'Booking created successfully',
            'booking': {'id': booking.id}
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bookings_bp.route('/<booking_id>/status', methods=['PUT'])
@jwt_required()
def update_booking_status(booking_id):
    """Update booking status"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    # Only agencies that own the booking can update status (e.g., pickup/return)
    agency = Agency.query.filter_by(user_id=user_id).first()
    if not agency or booking.agency_id != agency.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking.status = data['status']
    db.session.commit()
    
    return jsonify({'message': 'Booking status updated'}), 200

@bookings_bp.route('/<booking_id>/payment-status', methods=['PUT'])
@jwt_required()
def update_payment_status(booking_id):
    """Update booking payment status"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    if booking.customer_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking.payment_status = data['paymentStatus']
    db.session.commit()
    
    return jsonify({'message': 'Payment status updated'}), 200

@bookings_bp.route('/<booking_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_booking(booking_id):
    """Cancel a booking"""
    user_id = get_jwt_identity()
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    if booking.customer_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking.status = 'cancelled'
    if booking.payment_status == 'completed':
        booking.payment_status = 'refunded'
    
    db.session.commit()
    
    return jsonify({'message': 'Booking cancelled successfully'}), 200


@bookings_bp.route('/payment/order', methods=['POST'])
@jwt_required()
def create_payment_order():
    """Create a Razorpay order for a booking and store a payment record."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    booking_id = data.get('bookingId')

    if not booking_id:
        return jsonify({'error': 'bookingId is required'}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    if booking.customer_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    amount_override = data.get('amountPaise') or data.get('amount_paise')
    amount_paise = int(amount_override) if amount_override is not None else int(round((booking.total_amount or 0) * 100))
    if amount_paise <= 0:
        return jsonify({'error': 'Invalid booking amount'}), 400

    try:
        short_receipt = f"b_{booking.id}"[:40]
        order_resp = _create_razorpay_order(
            amount_paise,
            receipt=short_receipt,
            notes={
                'booking_id': booking.id,
                'vehicle_id': booking.vehicle_id,
                'customer_id': booking.customer_id,
            },
        )

        # Persist payment record
        payment = Payment(
            booking_id=booking.id,
            razorpay_order_id=order_resp.get('id'),
            amount=amount_paise,
            currency=order_resp.get('currency', 'INR'),
            status=order_resp.get('status', 'created'),
            notes=json.dumps(order_resp.get('notes', {})),
            raw_response=json.dumps(order_resp),
        )
        db.session.add(payment)
        booking.payment_status = 'pending'
        db.session.commit()

        return jsonify({
            'keyId': RAZORPAY_KEY_ID,
            'order': order_resp,
            'bookingId': booking.id,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bookings_bp.route('/payment/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    """Verify Razorpay signature and mark booking as paid."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    booking_id = data.get('bookingId')
    order_id = data.get('razorpay_order_id')
    payment_id = data.get('razorpay_payment_id')
    signature = data.get('razorpay_signature')

    if not all([booking_id, order_id, payment_id, signature]):
        return jsonify({'error': 'Missing payment verification fields'}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    if booking.customer_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    if not _verify_signature(order_id, payment_id, signature):
        return jsonify({'error': 'Invalid payment signature'}), 400

    # Update payment record
    payment = Payment.query.filter_by(razorpay_order_id=order_id).first()
    if not payment:
        payment = Payment(
            booking_id=booking.id,
            razorpay_order_id=order_id,
            amount=int(round((booking.total_amount or 0) * 100)),
            currency='INR',
        )
        db.session.add(payment)

    payment.razorpay_payment_id = payment_id
    payment.razorpay_signature = signature
    payment.status = 'paid'
    payment.raw_response = json.dumps(data)
    payment.email = data.get('email')
    payment.contact = data.get('contact')
    payment.method = data.get('method')

    booking.payment_status = 'completed'
    booking.status = 'confirmed'

    db.session.commit()

    return jsonify({'message': 'Payment verified successfully'}), 200


@bookings_bp.route('/payment/fail', methods=['POST'])
@jwt_required()
def fail_payment():
    """Record a failed Razorpay payment and mark booking/payment accordingly."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    booking_id = data.get('bookingId')
    order_id = data.get('razorpay_order_id')

    if not booking_id:
        return jsonify({'error': 'bookingId is required'}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    if booking.customer_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    payment = None
    if order_id:
        payment = Payment.query.filter_by(razorpay_order_id=order_id).first()

    if not payment:
        payment = Payment(
            booking_id=booking.id,
            razorpay_order_id=order_id or f"failed_{booking.id}",
            amount=int(round((booking.total_amount or 0) * 100)),
            currency='INR',
        )
        db.session.add(payment)

    payment.status = 'failed'
    payment.razorpay_payment_id = data.get('razorpay_payment_id')
    payment.razorpay_signature = data.get('razorpay_signature')
    payment.raw_response = json.dumps(data)
    payment.email = data.get('email')
    payment.contact = data.get('contact')
    payment.method = data.get('method')

    booking.payment_status = 'failed'
    booking.status = 'cancelled'

    db.session.commit()

    return jsonify({'message': 'Payment marked as failed; booking cancelled'}), 200
