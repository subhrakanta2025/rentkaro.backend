from flask import Blueprint, request, jsonify
from app.models.catalog import CatalogBrand, CatalogModel
from app import db

catalog_bp = Blueprint('catalog', __name__, url_prefix='/api/catalog')


@catalog_bp.route('/brands', methods=['GET'])
def list_brands():
    vehicle_type = request.args.get('vehicle_type')
    query = CatalogBrand.query
    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)

    brands = query.order_by(CatalogBrand.name.asc()).all()
    result = [{'id': b.id, 'name': b.name, 'vehicle_type': b.vehicle_type} for b in brands]
    return jsonify({'brands': result}), 200


@catalog_bp.route('/models', methods=['GET'])
def list_models():
    brand_id = request.args.get('brand_id')
    if not brand_id:
        return jsonify({'error': 'brand_id is required'}), 400

    models = CatalogModel.query.filter_by(brand_id=brand_id).order_by(CatalogModel.name.asc()).all()
    result = [{'id': m.id, 'name': m.name, 'brand_id': m.brand_id} for m in models]
    return jsonify({'models': result}), 200


@catalog_bp.route('/brands/<string:brand_id>/models', methods=['GET'])
def list_models_for_brand(brand_id: str):
    models = CatalogModel.query.filter_by(brand_id=brand_id).order_by(CatalogModel.name.asc()).all()
    result = [{'id': m.id, 'name': m.name} for m in models]
    return jsonify({'models': result}), 200
