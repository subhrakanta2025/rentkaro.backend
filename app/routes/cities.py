from flask import Blueprint, jsonify, request
from app.models import City

cities_bp = Blueprint('cities', __name__, url_prefix='/api/cities')


@cities_bp.route('', methods=['GET'])
def list_cities():
    """Return all cities or filter by a search query."""
    search_term = request.args.get('q', type=str)
    query = City.query

    if search_term:
        like_term = f"%{search_term.strip()}%"
        query = query.filter(City.name.ilike(like_term))

    cities = query.order_by(City.name.asc()).all()
    return jsonify({
        'cities': [
            {
                'id': city.id,
                'name': city.name,
                'slug': city.slug,
            }
            for city in cities
        ]
    })
