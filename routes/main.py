from flask import Blueprint, render_template, session, redirect, url_for
from models.fournisseur import Fournisseur

main = Blueprint('main', __name__)

@main.route('/')
def index():
    fournisseurs = Fournisseur.query.filter_by(is_active=True).order_by(Fournisseur.nom).all()
    return render_template('reception/index.html', fournisseurs=fournisseurs)

@main.route('/session-info')
def session_info():
    return {
        'reference': session.get('rec_reference', ''),
        'fournisseur': session.get('rec_fournisseur', ''),
        'lignes': session.get('rec_lignes', [])
    }
