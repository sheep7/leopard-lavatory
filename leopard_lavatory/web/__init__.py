import os

from flask import Flask


def create_app():
    # create and configure the app
    app = Flask(__name__)
    # secret key needed for signing session cookies
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')

    from leopard_lavatory.web import home
    app.register_blueprint(home.bp)

    return app
