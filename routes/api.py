from flask import Blueprint, request, jsonify, session
from models.article import Article
from models.article_barcode import ArticleBarcode
from models.reception import Reception, ReceptionLigne
from models.fournisseur import Fournisseur
from extensions import db
from datetime import datetime

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/articles', methods=['GET'])
def get_articles():
    """Return all active articles for local cache on PDA - FAST version"""
    # ONE query for all active articles
    articles = Article.query.filter_by(is_active=True).all()

    # ONE query for ALL extra barcodes (no per-article query)
    all_extras = ArticleBarcode.query.all()

    # Build dict: article_id -> list of extra barcodes
    extras_by_article = {}
    for eb in all_extras:
        if eb.article_id not in extras_by_article:
            extras_by_article[eb.article_id] = []
        extras_by_article[eb.article_id].append(eb.barcode)

    # Build response in memory - no more DB queries
    result = []
    for a in articles:
        # Collect all barcodes for this article
        all_barcodes = []
        if a.barcode:
            all_barcodes.append(a.barcode)
        for extra_bc in extras_by_article.get(a.id, []):
            if extra_bc not in all_barcodes:
                all_barcodes.append(extra_bc)

        if all_barcodes:
            for barcode in all_barcodes:
                result.append({
                    'id': a.id,
                    'code_article': a.code_article,
                    'designation': a.designation,
                    'barcode': barcode,
                    'unite': a.unite
                })
        else:
            result.append({
                'id': a.id,
                'code_article': a.code_article,
                'designation': a.designation,
                'barcode': None,
                'unite': a.unite
            })

    return jsonify({
        'success': True,
        'count': len(result),
        'articles': result
    })


@api.route('/lookup', methods=['GET'])
def lookup():
    """Lookup article by barcode - searches primary and extra barcodes"""
    barcode = request.args.get('barcode', '').strip()

    if not barcode:
        return jsonify({'found': False, 'message': 'Code-barres vide'})

    article = Article.query.filter_by(barcode=barcode, is_active=True).first()

    if not article:
        extra = ArticleBarcode.query.filter_by(barcode=barcode).first()
        if extra:
            article = db.session.get(Article, extra.article_id)
            if article and not article.is_active:
                article = None

    if not article:
        return jsonify({'found': False, 'message': 'Article non trouve'})

    return jsonify({
        'found': True,
        'article': {
            'id': article.id,
            'code_article': article.code_article,
            'designation': article.designation,
            'unite': article.unite,
            'barcode': barcode
        }
    })


@api.route('/add-ligne', methods=['POST'])
def add_ligne():
    """Add scanned article to current session"""
    data = request.get_json()
    article_id  = data.get('article_id')
    qte         = float(data.get('qte', 1))
    rec_id      = session.get('reception_id')

    if not rec_id:
        return jsonify({'success': False, 'message': 'Aucune reception active'})

    reception = db.session.get(Reception, rec_id)
    if not reception:
        return jsonify({'success': False, 'message': 'Reception introuvable'})

    existing = ReceptionLigne.query.filter_by(
        reception_id=rec_id,
        article_id=article_id
    ).first()

    was_existing = existing is not None
    old_qte = existing.qte_recue if existing else 0

    if existing:
        existing.qte_recue = qte
    else:
        ligne = ReceptionLigne(
            reception_id=rec_id,
            article_id=article_id,
            qte_recue=qte
        )
        db.session.add(ligne)

    db.session.commit()

    lignes = []
    for l in reception.lignes:
        lignes.append({
            'id': l.id,
            'code_article': l.article.code_article,
            'designation': l.article.designation,
            'unite': l.article.unite,
            'qte_recue': l.qte_recue
        })

    return jsonify({
        'success': True,
        'total_lignes': len(lignes),
        'lignes': lignes,
        'was_existing': was_existing,
        'old_qte': old_qte
    })


@api.route('/check-ligne', methods=['GET'])
def check_ligne():
    """Check if article already exists in current reception"""
    article_id = request.args.get('article_id', type=int)
    rec_id = session.get('reception_id')

    if not rec_id or not article_id:
        return jsonify({'exists': False})

    ligne = ReceptionLigne.query.filter_by(
        reception_id=rec_id,
        article_id=article_id
    ).first()

    if ligne:
        return jsonify({
            'exists': True,
            'qte': ligne.qte_recue
        })

    return jsonify({'exists': False})


@api.route('/start-reception', methods=['POST'])
def start_reception():
    """Start a new reception session"""
    data = request.get_json()
    fournisseur_id = data.get('fournisseur_id')
    notes = data.get('notes', '')

    reference = Reception.generate_reference()

    reception = Reception(
        reference=reference,
        fournisseur_id=fournisseur_id if fournisseur_id else None,
        notes=notes,
        date_reception=datetime.utcnow().date(),
        statut='en_cours'
    )
    db.session.add(reception)
    db.session.commit()

    session['reception_id'] = reception.id
    session['reception_ref'] = reference

    return jsonify({
        'success': True,
        'reception_id': reception.id,
        'reference': reference
    })


@api.route('/finish-reception', methods=['POST'])
def finish_reception():
    """Mark reception as finished"""
    rec_id = session.get('reception_id')
    if not rec_id:
        return jsonify({'success': False, 'message': 'Aucune reception active'})

    reception = db.session.get(Reception, rec_id)
    if reception:
        reception.statut = 'terminee'
        db.session.commit()

    session.pop('reception_id', None)
    session.pop('reception_ref', None)

    return jsonify({
        'success': True,
        'reference': reception.reference if reception else ''
    })


@api.route('/current-reception')
def current_reception():
    """Get current reception data"""
    rec_id = session.get('reception_id')
    if not rec_id:
        return jsonify({'active': False})

    reception = db.session.get(Reception, rec_id)
    if not reception:
        session.pop('reception_id', None)
        return jsonify({'active': False})

    lignes = []
    for l in reception.lignes:
        lignes.append({
            'id': l.id,
            'code_article': l.article.code_article,
            'designation': l.article.designation,
            'unite': l.article.unite,
            'qte_recue': l.qte_recue
        })

    return jsonify({
        'active': True,
        'reception_id': reception.id,
        'reference': reception.reference,
        'fournisseur': reception.fournisseur.nom if reception.fournisseur else None,
        'total_lignes': len(lignes),
        'lignes': lignes
    })


@api.route('/remove-ligne/<int:ligne_id>', methods=['DELETE'])
def remove_ligne(ligne_id):
    """Remove a ligne from current reception"""
    rec_id = session.get('reception_id')
    ligne = db.session.get(ReceptionLigne, ligne_id)

    if not ligne or ligne.reception_id != rec_id:
        return jsonify({'success': False, 'message': 'Ligne introuvable'})

    db.session.delete(ligne)
    db.session.commit()

    return jsonify({'success': True})