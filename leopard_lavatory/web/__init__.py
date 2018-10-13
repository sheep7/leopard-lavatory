"""Web module - flask app that serves the website."""

import os

from flask import Flask


def create_app():
    """Create and configure the flask app."""
    app = Flask(__name__)

    # secret key needed for signing session cookies
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')

    from leopard_lavatory.web import main
    app.register_blueprint(main.bp)

    return app
