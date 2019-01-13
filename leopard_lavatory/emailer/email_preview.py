"""Email preview - flask app that renders email template previews."""

import logging
import os

from flask import Blueprint, Flask
from flask import abort, render_template

from leopard_lavatory.emailer import TEMPLATES, DEFAULT_DATA, create_email_bodies

LOG = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Render the email template preview index page listing all available templates.
    Returns:
        Union[str, werkzeug.wrappers.Response]: a rendered template or a werkzeug Response object
    """
    return render_template('index.html', templates=TEMPLATES, default_data=DEFAULT_DATA)


@bp.route('/<template>')
def preview_template(template):
    """Render a template.
    Returns:
        Union[str, werkzeug.wrappers.Response]: a rendered template or a werkzeug Response object
    """
    if template not in TEMPLATES:
        abort(404)

    txt_body, html_body = create_email_bodies(template)

    combined = f'{html_body[:-15]}<hr style="margin: 30px 0 0 0"><p>text-only version:</p>' \
        f'<div style="margin: 50px"><pre>{txt_body}</pre></div></body></html>'

    return combined


def create_app():
    """Create and configure the flask app."""
    app = Flask(__name__)

    # secret key needed for signing session cookies
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')

    app.register_blueprint(bp)

    return app
