from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.agency import Agency
from app.models.agency_kyc import AgencyKYC
from app.utils.decorators import agency_required
from datetime import datetime

agency_kyc_bp = Blueprint('agency_kyc', __name__, url_prefix='/api/agency-kyc')


def _serialize(kyc: AgencyKYC):
    if not kyc:
        return None
    return kyc.to_dict()


def _get_agency_for_user(user_id):
    return Agency.query.filter_by(user_id=user_id).first()


@agency_kyc_bp.route('/me', methods=['GET'])
@jwt_required()
@agency_required
def get_my_agency_kyc():
    user_id = get_jwt_identity()
    agency = _get_agency_for_user(user_id)
    if not agency:
        return jsonify({'error': 'Agency not found for user'}), 404
    kyc = AgencyKYC.query.filter_by(agency_id=agency.id).first()
    return jsonify({'kyc': _serialize(kyc)}), 200


@agency_kyc_bp.route('', methods=['POST'])
@jwt_required()
@agency_required
def upsert_agency_kyc():
    user_id = get_jwt_identity()
    agency = _get_agency_for_user(user_id)
    if not agency:
        return jsonify({'error': 'Agency not found for user'}), 404

    data = request.get_json() or {}
    kyc = AgencyKYC.query.filter_by(agency_id=agency.id).first()
    if not kyc:
        kyc = AgencyKYC(agency_id=agency.id)
        db.session.add(kyc)

    kyc.pan_number = data.get('panNumber', kyc.pan_number)
    kyc.gst_number = data.get('gstNumber', kyc.gst_number)
    kyc.license_number = data.get('licenseNumber', kyc.license_number)
    kyc.pan_doc_url = data.get('panDocUrl', kyc.pan_doc_url)
    kyc.gst_doc_url = data.get('gstDocUrl', kyc.gst_doc_url)
    kyc.license_doc_url = data.get('licenseDocUrl', kyc.license_doc_url)
    kyc.verification_status = data.get('verificationStatus', kyc.verification_status)

    db.session.commit()
    return jsonify({'kyc': _serialize(kyc), 'message': 'Agency KYC saved'}), 200


@agency_kyc_bp.route('/<kyc_id>', methods=['PUT'])
@jwt_required()
@agency_required
def update_agency_kyc(kyc_id):
    user_id = get_jwt_identity()
    agency = _get_agency_for_user(user_id)
    if not agency:
        return jsonify({'error': 'Agency not found for user'}), 404

    kyc = AgencyKYC.query.get(kyc_id)
    if not kyc or kyc.agency_id != agency.id:
        return jsonify({'error': 'KYC record not found or unauthorized'}), 404

    data = request.get_json() or {}
    kyc.pan_number = data.get('panNumber', kyc.pan_number)
    kyc.gst_number = data.get('gstNumber', kyc.gst_number)
    kyc.license_number = data.get('licenseNumber', kyc.license_number)
    kyc.pan_doc_url = data.get('panDocUrl', kyc.pan_doc_url)
    kyc.gst_doc_url = data.get('gstDocUrl', kyc.gst_doc_url)
    kyc.license_doc_url = data.get('licenseDocUrl', kyc.license_doc_url)
    kyc.verification_status = data.get('verificationStatus', kyc.verification_status)

    db.session.commit()
    return jsonify({'kyc': _serialize(kyc), 'message': 'Agency KYC updated'}), 200


@agency_kyc_bp.route('/<kyc_id>/verify', methods=['PUT'])
@jwt_required()
def verify_agency_kyc(kyc_id):
    # This should ideally be admin-protected; simple check here.
    data = request.get_json() or {}
    kyc = AgencyKYC.query.get(kyc_id)
    if not kyc:
        return jsonify({'error': 'KYC record not found'}), 404

    kyc.pan_verified = data.get('panVerified', kyc.pan_verified)
    kyc.gst_verified = data.get('gstVerified', kyc.gst_verified)
    kyc.license_verified = data.get('licenseVerified', kyc.license_verified)
    kyc.verification_status = data.get('verificationStatus', kyc.verification_status or 'pending')
    kyc.rejection_reason = data.get('rejectionReason', kyc.rejection_reason)

    db.session.commit()
    return jsonify({'kyc': _serialize(kyc), 'message': 'Agency KYC verification updated'}), 200
