from sqlalchemy import inspect, text

from app import db


def ensure_schema_consistency() -> None:
    """Apply lightweight schema fixes for deployments without migrations."""
    inspector = inspect(db.engine)

    def column_exists(table: str, column: str) -> bool:
        return any(col['name'] == column for col in inspector.get_columns(table))

    # Add avatar_locked to profiles if missing
    if not column_exists('profiles', 'avatar_locked'):
        db.session.execute(text("ALTER TABLE profiles ADD COLUMN avatar_locked BOOLEAN DEFAULT 0"))
        db.session.commit()
        inspector = inspect(db.engine)

    # Add selfie_document_url to kyc_verifications if missing
    if not column_exists('kyc_verifications', 'selfie_document_url'):
        db.session.execute(text("ALTER TABLE kyc_verifications ADD COLUMN selfie_document_url VARCHAR(255)"))
        db.session.commit()
        inspector = inspect(db.engine)

    # Add documents_uploaded to kyc_verifications if missing
    if not column_exists('kyc_verifications', 'documents_uploaded'):
        db.session.execute(text("ALTER TABLE kyc_verifications ADD COLUMN documents_uploaded BOOLEAN DEFAULT 0"))
        db.session.commit()
        inspector = inspect(db.engine)

    # Add admin_user_id to agencies if missing
    if not column_exists('agencies', 'admin_user_id'):
        db.session.execute(text("ALTER TABLE agencies ADD COLUMN admin_user_id VARCHAR(36)"))
        db.session.commit()
        inspector = inspect(db.engine)

    # Add gst_doc_url to agencies if missing
    if not column_exists('agencies', 'gst_doc_url'):
        db.session.execute(text("ALTER TABLE agencies ADD COLUMN gst_doc_url VARCHAR(255)"))
        db.session.commit()
        inspector = inspect(db.engine)

    # Add business_photo_url to agencies if missing
    if not column_exists('agencies', 'business_photo_url'):
        db.session.execute(text("ALTER TABLE agencies ADD COLUMN business_photo_url VARCHAR(255)"))
        db.session.commit()
        inspector = inspect(db.engine)

    # Add new specification columns to vehicles if missing
    if not column_exists('vehicles', 'displacement'):
        db.session.execute(text("ALTER TABLE vehicles ADD COLUMN displacement VARCHAR(50)"))
        db.session.commit()
        inspector = inspect(db.engine)

    if not column_exists('vehicles', 'top_speed'):
        db.session.execute(text("ALTER TABLE vehicles ADD COLUMN top_speed VARCHAR(50)"))
        db.session.commit()
        inspector = inspect(db.engine)

    if not column_exists('vehicles', 'fuel_capacity'):
        db.session.execute(text("ALTER TABLE vehicles ADD COLUMN fuel_capacity VARCHAR(50)"))
        db.session.commit()
        inspector = inspect(db.engine)

    if not column_exists('vehicles', 'weight'):
        db.session.execute(text("ALTER TABLE vehicles ADD COLUMN weight VARCHAR(50)"))
        db.session.commit()
        inspector = inspect(db.engine)

    if not column_exists('vehicles', 'late_fee_per_hr'):
        db.session.execute(text("ALTER TABLE vehicles ADD COLUMN late_fee_per_hr FLOAT"))
        db.session.commit()
        inspector = inspect(db.engine)

    if not column_exists('vehicles', 'excess_per_km'):
        db.session.execute(text("ALTER TABLE vehicles ADD COLUMN excess_per_km FLOAT"))
        db.session.commit()
        inspector = inspect(db.engine)

    if not column_exists('vehicles', 'timings'):
        db.session.execute(text("ALTER TABLE vehicles ADD COLUMN timings VARCHAR(100)"))
        db.session.commit()
        inspector = inspect(db.engine)
