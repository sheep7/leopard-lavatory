from flask import Blueprint, flash, render_template, request

bp = Blueprint('home', __name__)


@bp.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        address = request.form['address']
        email = request.form['email']
        flash(f'Not implemented yet (got address: {address} and email: {email})')
        return render_template('index.html')

    if request.method == 'GET':
        return render_template('index.html')
