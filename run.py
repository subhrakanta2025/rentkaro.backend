#!/usr/bin/env python3
"""Main Flask Application Entry Point"""

import os
from dotenv import load_dotenv

# Load environment variables before importing the app so config.py reads them
load_dotenv()

from app import create_app

# Instantiate once so gunicorn (run:app) can import it
app = create_app()

def main():
    """Run the Flask dev server when executed directly."""
    port = int(os.getenv('FLASK_PORT', 8085))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_ENV') == 'development'
    )


if __name__ == '__main__':
    main()
