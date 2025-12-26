from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import get_config
import os

db = SQLAlchemy()
jwt = JWTManager()
mail_cache = {}  # Temporary cache for OTP storage

def create_app():
    """Application factory"""
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Set upload directory
    app.config['UPLOAD_DIR'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.vehicles import vehicles_bp
    from app.routes.bookings import bookings_bp
    from app.routes.agencies import agencies_bp
    from app.routes.kyc import kyc_bp
    from app.routes.cities import cities_bp
    from app.routes.catalog import catalog_bp
    from app.routes.uploads import uploads_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(agencies_bp)
    app.register_blueprint(kyc_bp)
    app.register_blueprint(cities_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(uploads_bp)
    
    # Serve uploaded files
    @app.route('/uploads/<path:filepath>')
    def serve_upload(filepath):
        from flask import send_from_directory
        upload_dir = app.config.get('UPLOAD_DIR')
        return send_from_directory(upload_dir, filepath, as_attachment=False)
    
    # Create tables
    with app.app_context():
        try:
            # Import models so SQLAlchemy knows about them
            from app.models import payment  # noqa: F401

            db.create_all()
            from app.utils.seed_cities import seed_cities
            from app.utils.schema import ensure_schema_consistency
            # Seed vehicle catalogs
            from app.utils.seed_catalog import seed_catalogs
            seed_cities()
            ensure_schema_consistency()
            try:
                seed_catalogs()
            except Exception as e:
                app.logger.exception('Failed to seed catalogs: %s', e)
        except Exception as e:
            app.logger.error('Database initialization failed: %s', e)
            app.logger.warning('App will continue but database operations may fail')
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return {'status': 'ok'}, 200
    
    return app
