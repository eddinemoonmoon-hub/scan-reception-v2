from flask import Blueprint, render_template

verify = Blueprint('verify', __name__)


@verify.route('/verify')
def index():
    return render_template('verify/index.html')


@verify.route('/verify/scan')
def scan():
    return render_template('verify/scan.html')


@verify.route('/verify/log')
def log():
    return render_template('verify/log.html')