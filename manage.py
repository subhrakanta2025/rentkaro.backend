#!/usr/bin/env python3
"""Flask-Migrate CLI helper."""
import os
from dotenv import load_dotenv
from flask.cli import FlaskGroup
from flask_migrate import Migrate
import click

load_dotenv()

from app import create_app, db

def create_my_app():
    app = create_app()
    Migrate(app, db)
    return app

cli = FlaskGroup(create_app=create_my_app)

@cli.command('seed-catalog')
def seed_catalog_command():
    """Seed vehicle catalogs (bikes and cars)."""
    from app.utils.seed_catalog import seed_catalogs
    click.echo('Seeding vehicle catalogs...')
    try:
        seed_catalogs()
        click.echo('✓ Catalogs seeded successfully!')
    except Exception as e:
        click.echo(f'✗ Error seeding catalogs: {e}', err=True)
        raise

@cli.command('seed-cities')
def seed_cities_command():
    """Seed cities data."""
    from app.utils.seed_cities import seed_cities
    click.echo('Seeding cities...')
    try:
        seed_cities()
        click.echo('✓ Cities seeded successfully!')
    except Exception as e:
        click.echo(f'✗ Error seeding cities: {e}', err=True)
        raise

if __name__ == '__main__':
    cli()
