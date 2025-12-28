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
    # Ensure instance directory exists and sqlite db file is writable when using file-based sqlite
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '') or ''
    if db_uri.startswith('sqlite:///') and not db_uri.startswith('sqlite:////'):
        # paths like sqlite:///instance/ride_rentals.db -> file path is relative to app.root_path
        db_path = db_uri.replace('sqlite:///', '')
        # If it's not an absolute path, make sure it's under the project root
        if not os.path.isabs(db_path):
            instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
            instance_dir = os.path.normpath(instance_dir)
            os.makedirs(instance_dir, exist_ok=True)
            full_db_path = os.path.join(instance_dir, os.path.basename(db_path))
        else:
            full_db_path = db_path

        try:
            # Create empty file if not exists and ensure writable
            if not os.path.exists(full_db_path):
                open(full_db_path, 'a').close()
            # Try opening for append to test writability
            with open(full_db_path, 'a'):
                pass
        except Exception as ex:
            app.logger.error('Failed to ensure sqlite database file is writable: %s', ex)
            app.logger.warning('If running in a read-only filesystem (for example in some cloud builds), set DATABASE_URL to a writable DB.')
    
    # Set upload directory. Prefer a writable location in cloud environments (/tmp)
    default_upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    preferred_tmp = os.getenv('UPLOAD_DIR') or os.getenv('TMPDIR') or os.getenv('TMP') or os.getenv('TEMP') or '/tmp'
    # If preferred_tmp exists and is writable, use it under a subfolder, otherwise fall back to project uploads
    chosen_upload = default_upload_dir
    try:
        tmp_candidate = os.path.join(preferred_tmp, 'rentkaro_uploads')
        os.makedirs(tmp_candidate, exist_ok=True)
        # test writability
        testfile = os.path.join(tmp_candidate, '.write_test')
        with open(testfile, 'w') as f:
            f.write('ok')
        os.remove(testfile)
        chosen_upload = tmp_candidate
    except Exception:
        # fallback to project uploads directory
        try:
            os.makedirs(default_upload_dir, exist_ok=True)
            testfile = os.path.join(default_upload_dir, '.write_test')
            with open(testfile, 'w') as f:
                f.write('ok')
            os.remove(testfile)
            chosen_upload = default_upload_dir
        except Exception as ex:
            app.logger.error('No writable upload directory found: %s', ex)
            # Last resort: use current working directory under uploads
            cwd_upload = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(cwd_upload, exist_ok=True)
            chosen_upload = cwd_upload

    app.config['UPLOAD_DIR'] = chosen_upload
    
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
