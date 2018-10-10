from flask import Blueprint, flash, render_template, request
from leopard_lavatory.web.tasks import add_together

bp = Blueprint('home', __name__)

@bp.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        address = request.form['address']
        email = request.form['email']
        flash(f'Not implemented yet (got address: {address} and email: {email})')
        return render_template('index.html')

    if request.method == 'GET':
        result = add_together.delay(23, 42)
        result.wait()  # 65
        print(result.result)
        return render_template('index.html')
