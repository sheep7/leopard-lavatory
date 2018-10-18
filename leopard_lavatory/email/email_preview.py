"""Email preview - flask app that renders email template previews."""

import logging
import os

import yaml
from flask import Blueprint, Flask
from flask import abort, render_template

LOG = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

TEMPLATES = []
DEFAULT_VALUES = {}


def read_templates():
    """Reads the available templates from the template directory and stores them in
    the global TEMPLATES variable, a list of template names
    (without file endings and excluding index).

    It also tries to read yml files with default values for each of the html templates
    and if found, stores them in the DEFAULT_VALUES dictionary.
    """
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(current_file_path, 'templates')
    template_files = os.listdir(templates_path)
    for file in template_files:
        if file.endswith('.html') and not file == 'index.html':
            TEMPLATES.append(file[:-5])
        if file.endswith('.yml'):
            DEFAULT_VALUES[file[:-4]] = yaml.safe_load(open(os.path.join(templates_path, file)))


read_templates()


@bp.route('/')
def index():
    """Render the email template preview index page listing all available templates.
    Returns:
        Union[str, werkzeug.wrappers.Response]: a rendered template or a werkzeug Response object
    """
    return render_template('index.html', templates=TEMPLATES)


@bp.route('/<template>')
def preview_template(template):
    """Render a template.
    Returns:
        Union[str, werkzeug.wrappers.Response]: a rendered template or a werkzeug Response object
    """
    if template not in TEMPLATES:
        abort(404)

    return render_template(f'{template}.html', **DEFAULT_VALUES.get(template, {}))


def create_app():
    """Create and configure the flask app."""
    app = Flask(__name__)

    # secret key needed for signing session cookies
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')

    app.register_blueprint(bp)

    return app
