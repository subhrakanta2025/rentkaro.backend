from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.feedback import Feedback
from app.models.booking import Booking

feedbacks_bp = Blueprint('feedbacks', __name__, url_prefix='/api/feedbacks')


@feedbacks_bp.route('', methods=['POST'])
@jwt_required()
def create_feedback():
    """Create feedback for a booking. Expects JSON: {bookingId, rating, comment}
    Rating should be integer (1-5)."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    booking_id = data.get('bookingId')
    rating = data.get('rating')
    comment = data.get('comment')

    if not booking_id or rating is None:
        return jsonify({'error': 'bookingId and rating are required'}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    # Only the booking customer can submit feedback
    if booking.customer_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Ensure booking status is completed
    if booking.status != 'completed':
        return jsonify({'error': 'Feedback can be submitted only after booking is completed'}), 400

    try:
        fb = Feedback(
            booking_id=booking_id,
            customer_id=user_id,
            agency_id=booking.agency_id,
            rating=int(rating),
            comment=comment
        )
        db.session.add(fb)
        db.session.commit()
        return jsonify({'message': 'Feedback submitted', 'feedback': fb.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@feedbacks_bp.route('', methods=['GET'])
def list_feedbacks():
    """List feedbacks with optional filters: ?agency_id=&customer_id=&booking_id="""
    agency_id = request.args.get('agency_id')
    customer_id = request.args.get('customer_id')
    booking_id = request.args.get('booking_id')

    query = Feedback.query
    if agency_id:
        query = query.filter_by(agency_id=agency_id)
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if booking_id:
        query = query.filter_by(booking_id=booking_id)

    feedbacks = query.order_by(Feedback.created_at.desc()).all()
    return jsonify({'feedbacks': [f.to_dict() for f in feedbacks]}), 200
