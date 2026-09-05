from flask import Blueprint, render_template

economat = Blueprint('economat', __name__)

@economat.route('/economat/scan')
def scan():
    return render_template('economat/scan.html')

@economat.route('/economat/log')
def log():
    return render_template('economat/log.html')