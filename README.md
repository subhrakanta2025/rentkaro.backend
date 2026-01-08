Database migrations
-------------------

This project uses Flask-Migrate (Alembic) for database migrations. To create and apply migrations locally, run the following from the project root after activating your Python environment and ensuring `requirements.txt` is installed:

```bash
python -m pip install -r requirements.txt
python manage.py db init        # run once to initialize the migrations directory
python manage.py db migrate -m "Initial migration"
python manage.py db upgrade
```

Notes:
- Do not run `db init` more than once; if a `migrations/` folder already exists, skip `db init`.
- The app reads DB configuration from `.env`. Make sure `.env` points to your MySQL instance if you want to run migrations against it.
# rentkaro.backend