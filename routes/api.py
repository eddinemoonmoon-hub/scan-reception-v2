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

# ─── STOCK LEVELS (from local TCPOS bridge) ─────────────

@api.route('/stock-sync', methods=['POST'])
def stock_sync():
    """Receive bulk stock data from local bridge script"""
    import os
    from models.stock_level import StockLevel

    sync_key = request.headers.get('X-Sync-Key', '')
    expected_key = os.environ.get('SYNC_API_KEY', 'pmd-sync-2026-v2-staging')
    if sync_key != expected_key:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.get_json()
    warehouse = data.get('warehouse', '20')
    stock_items = data.get('stock', [])

    if not stock_items:
        return jsonify({'success': False, 'message': 'No stock data'})

    existing = {sl.article_code: sl for sl in StockLevel.query.filter_by(warehouse_code=warehouse).all()}

    # Deduplicate incoming items - keep last qty for each code
    incoming = {}
    for item in stock_items:
        code = str(item.get('code', '')).strip()
        if not code:
            continue
        try:
            qty = float(item.get('qty', 0))
        except (TypeError, ValueError):
            continue
        incoming[code] = qty  # last one wins if duplicate

    updated = 0
    new_items = []
    now = datetime.utcnow()

    for code, qty in incoming.items():
        if code in existing:
            existing[code].quantity = qty
            existing[code].updated_at = now
        else:
            new_items.append(StockLevel(
                article_code=code,
                warehouse_code=warehouse,
                quantity=qty
            ))
        updated += 1

    if new_items:
        db.session.bulk_save_objects(new_items)

    db.session.commit()
    return jsonify({'success': True, 'updated': updated, 'unique_codes': len(incoming)})


@api.route('/stock-level', methods=['GET'])
def stock_level():
    """Get stock level for an article from local cache"""
    from models.stock_level import StockLevel

    article_code = request.args.get('article_code', '').strip()
    warehouse = request.args.get('warehouse', '20')

    if not article_code:
        return jsonify({'found': False})

    sl = StockLevel.query.filter_by(
        article_code=article_code,
        warehouse_code=warehouse
    ).first()

    if sl:
        return jsonify({
            'found': True,
            'quantity': sl.quantity,
            'updated_at': sl.updated_at.strftime('%d/%m/%Y %H:%M') if sl.updated_at else None
        })

    return jsonify({'found': False, 'quantity': 0})


# ─── INVENTAIRE / VERIFY ────────────────────────────────

@api.route('/start-inventaire', methods=['POST'])
def start_inventaire():
    """Start a new inventaire session"""
    from models.inventaire import Inventaire

    data = request.get_json()
    agent_name = (data.get('agent_name', '') or '').strip()
    notes = data.get('notes', '')

    reference = Inventaire.generate_reference()

    inv = Inventaire(
        reference=reference,
        warehouse_code='20',
        agent_name=agent_name if agent_name else None,
        notes=notes,
        date_inventaire=datetime.utcnow().date(),
        statut='en_cours'
    )
    db.session.add(inv)
    db.session.commit()

    session['inventaire_id'] = inv.id
    session['inventaire_ref'] = reference

    return jsonify({
        'success': True,
        'inventaire_id': inv.id,
        'reference': reference
    })


@api.route('/current-inventaire')
def current_inventaire():
    """Get current inventaire session"""
    from models.inventaire import Inventaire

    inv_id = session.get('inventaire_id')
    if not inv_id:
        return jsonify({'active': False})

    inv = db.session.get(Inventaire, inv_id)
    if not inv:
        session.pop('inventaire_id', None)
        return jsonify({'active': False})

    lignes = []
    for l in inv.lignes:
        lignes.append({
            'id': l.id,
            'code_article': l.article.code_article,
            'designation': l.article.designation,
            'qte_systeme': l.qte_systeme,
            'qte_physique': l.qte_physique,
            'ecart': l.ecart,
            'scanned_at': l.scanned_at.strftime('%H:%M') if l.scanned_at else None
        })

    return jsonify({
        'active': True,
        'inventaire_id': inv.id,
        'reference': inv.reference,
        'agent_name': inv.agent_name,
        'total_lignes': len(lignes),
        'total_ecarts': inv.total_ecarts,
        'lignes': lignes
    })


@api.route('/add-inventaire-ligne', methods=['POST'])
def add_inventaire_ligne():
    """Add a comparison line to current inventaire (allow multiple counts)"""
    from models.inventaire import Inventaire, InventaireLigne
    from models.stock_level import StockLevel

    data = request.get_json()
    article_id = data.get('article_id')
    try:
        qte_physique = float(data.get('qte_physique', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Quantite invalide'})

    inv_id = session.get('inventaire_id')

    if not inv_id:
        return jsonify({'success': False, 'message': 'Aucun inventaire actif'})

    inv = db.session.get(Inventaire, inv_id)
    if not inv:
        return jsonify({'success': False, 'message': 'Inventaire introuvable'})

    article = db.session.get(Article, article_id)
    if not article:
        return jsonify({'success': False, 'message': 'Article introuvable'})

    sl = StockLevel.query.filter_by(
        article_code=article.code_article,
        warehouse_code='20'
    ).first()
    qte_systeme = sl.quantity if sl else 0
    ecart = qte_physique - qte_systeme

    ligne = InventaireLigne(
        inventaire_id=inv_id,
        article_id=article_id,
        qte_systeme=qte_systeme,
        qte_physique=qte_physique,
        ecart=ecart
    )
    db.session.add(ligne)
    db.session.commit()

    return jsonify({
        'success': True,
        'total_lignes': inv.total_lignes,
        'total_ecarts': inv.total_ecarts,
        'qte_systeme': qte_systeme,
        'ecart': ecart
    })


@api.route('/finish-inventaire', methods=['POST'])
def finish_inventaire():
    """Finish current inventaire session"""
    from models.inventaire import Inventaire

    inv_id = session.get('inventaire_id')
    if not inv_id:
        return jsonify({'success': False, 'message': 'Aucun inventaire actif'})

    inv = db.session.get(Inventaire, inv_id)
    if inv:
        inv.statut = 'terminee'
        db.session.commit()

    session.pop('inventaire_id', None)
    session.pop('inventaire_ref', None)

    return jsonify({
        'success': True,
        'reference': inv.reference if inv else ''
    })
