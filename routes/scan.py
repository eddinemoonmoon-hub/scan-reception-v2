from flask import Blueprint, render_template, session, redirect, url_for

scan = Blueprint('scan', __name__)

@scan.route('/scan')
def index():
    rec_id = session.get('reception_id')
    if not rec_id:
        return redirect(url_for('main.index'))
    return render_template('reception/scan.html')

@scan.route('/log')
def log():
    rec_id = session.get('reception_id')
    if not rec_id:
        return redirect(url_for('main.index'))
    return render_template('reception/log.html')
