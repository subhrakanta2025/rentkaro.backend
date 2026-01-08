from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import get_config
import os

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
mail_cache = {}  # Temporary cache for OTP storage

def create_app():
    """Application factory"""
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    # Log ZeptoMail key presence for debugging
    zkey = app.config.get('ZEPTOMAIL_API_KEY')
    if zkey:
        masked = zkey.strip()[:6] + '...' + zkey.strip()[-6:]
        app.logger.info('ZeptoMail API key present: %s', masked)
    else:
        app.logger.warning('ZeptoMail API key not present in configuration')
    # No file-based sqlite handling: app expects a full DATABASE_URL or DB_* vars to be set.
    
    # Set upload directory to project uploads by default (simple behavior)
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    app.config['UPLOAD_DIR'] = upload_dir
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
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
    from app.routes.agency_kyc import agency_kyc_bp
    from app.routes.feedbacks import feedbacks_bp
    from app.routes.kyc import kyc_bp
    from app.routes.cities import cities_bp
    from app.routes.catalog import catalog_bp
    # Register uploads blueprint only if google-cloud-storage is available
    try:
        from app.routes.uploads import uploads_bp
        app.register_blueprint(uploads_bp)
    except Exception:
        app.logger.warning('Uploads blueprint not registered (GCS client may be missing or misconfigured)')
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(agencies_bp)
    app.register_blueprint(agency_kyc_bp)
    app.register_blueprint(kyc_bp)
    app.register_blueprint(cities_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(feedbacks_bp)
    
    
    # Serve uploaded files
    @app.route('/uploads/<path:filepath>')
    def serve_upload(filepath):
        from flask import send_from_directory
        upload_dir = app.config.get('UPLOAD_DIR')
        return send_from_directory(upload_dir, filepath, as_attachment=False)
    
    # Create tables and seed data only when explicitly enabled.
    # To enable automatic DB initialization set the environment variable AUTO_INIT_DB
    # to '1' or 'true'. This avoids accidental schema creation in production.
    auto_init = os.getenv('AUTO_INIT_DB', 'false').lower() in ('1', 'true', 'yes')
    if auto_init:
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
    else:
        app.logger.info('AUTO_INIT_DB not set; skipping automatic database creation and seeding')
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return {'status': 'ok'}, 200
    
    return app
