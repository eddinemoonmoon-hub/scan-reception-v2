from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
from models.article import Article
from models.fournisseur import Fournisseur
from models.reception import Reception, ReceptionLigne
from extensions import db
from functools import wraps
import csv
import io
from datetime import datetime, date

admin = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_PASSWORD = 'admin123'

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


# --- AUTH -----------------------------------------------

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('is_admin'):
        return redirect(url_for('admin.dashboard'))
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'Mot de passe incorrect'
    return render_template('admin/login.html', error=error)


@admin.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin.login'))


# --- DASHBOARD ------------------------------------------

@admin.route('/')
@admin.route('/dashboard')
@admin_required
def dashboard():
    total_articles   = Article.query.filter_by(is_active=True).count()
    total_fournisseurs = Fournisseur.query.filter_by(is_active=True).count()
    total_receptions = Reception.query.count()
    recent_receptions = Reception.query.order_by(Reception.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_articles=total_articles,
                           total_fournisseurs=total_fournisseurs,
                           total_receptions=total_receptions,
                           recent_receptions=recent_receptions)


# --- ARTICLES -------------------------------------------

@admin.route('/articles')
@admin_required
def articles():
    search = request.args.get('q', '')
    query = Article.query
    if search:
        query = query.filter(
            db.or_(
                Article.designation.ilike(f'%{search}%'),
                Article.code_article.ilike(f'%{search}%'),
                Article.barcode.ilike(f'%{search}%')
            )
        )
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Article.designation).paginate(page=page, per_page=100, error_out=False)
    articles = pagination.items
    return render_template("admin/articles/list.html", articles=articles, search=search, pagination=pagination)


@admin.route('/articles/new', methods=['GET', 'POST'])
@admin_required
def article_new():
    if request.method == 'POST':
        code    = request.form.get('code_article', '').strip()
        desig   = request.form.get('designation', '').strip()
        barcode = request.form.get('barcode', '').strip()
        unite   = request.form.get('unite', 'piece').strip()

        if not code or not desig:
            flash('Code article et designation sont obligatoires', 'error')
            return render_template('admin/articles/form.html', article=None)

        existing_code = Article.query.filter_by(code_article=code).first()
        if existing_code:
            flash('Ce code article existe deja', 'error')
            return render_template('admin/articles/form.html', article=None)

        if barcode:
            existing_barcode = Article.query.filter_by(barcode=barcode).first()
            if existing_barcode:
                flash('Ce code-barres existe deja', 'error')
                return render_template('admin/articles/form.html', article=None)

        article = Article(
            code_article=code,
            designation=desig,
            barcode=barcode if barcode else None,
            unite=unite
        )
        db.session.add(article)
        db.session.commit()
        flash('Article cree avec succes', 'success')
        return redirect(url_for('admin.articles'))

    return render_template('admin/articles/form.html', article=None)


@admin.route('/articles/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def article_edit(id):
    article = db.session.get(Article, id)
    if not article:
        flash('Article introuvable', 'error')
        return redirect(url_for('admin.articles'))

    if request.method == 'POST':
        code    = request.form.get('code_article', '').strip()
        desig   = request.form.get('designation', '').strip()
        barcode = request.form.get('barcode', '').strip()
        unite   = request.form.get('unite', 'piece').strip()

        if not code or not desig:
            flash('Code article et designation sont obligatoires', 'error')
            return render_template('admin/articles/form.html', article=article)

        existing_code = Article.query.filter(
            Article.code_article == code,
            Article.id != id
        ).first()
        if existing_code:
            flash('Ce code article existe deja', 'error')
            return render_template('admin/articles/form.html', article=article)

        if barcode:
            existing_barcode = Article.query.filter(
                Article.barcode == barcode,
                Article.id != id
            ).first()
            if existing_barcode:
                flash('Ce code-barres existe deja', 'error')
                return render_template('admin/articles/form.html', article=article)

        article.code_article = code
        article.designation  = desig
        article.barcode      = barcode if barcode else None
        article.unite        = unite
        db.session.commit()
        flash('Article mis a jour', 'success')
        return redirect(url_for('admin.articles'))

    return render_template('admin/articles/form.html', article=article)


@admin.route('/articles/<int:id>/toggle', methods=['POST'])
@admin_required
def article_toggle(id):
    article = db.session.get(Article, id)
    if article:
        article.is_active = not article.is_active
        db.session.commit()
    return redirect(url_for('admin.articles'))


@admin.route('/articles/<int:id>/delete', methods=['POST'])
@admin_required
def article_delete(id):
    article = db.session.get(Article, id)
    if article:
        if article.lignes:
            flash('Impossible de supprimer: article utilise dans des receptions', 'error')
            return redirect(url_for('admin.articles'))
        db.session.delete(article)
        db.session.commit()
        flash('Article supprime', 'success')
    return redirect(url_for('admin.articles'))
@admin.route('/articles/cleanup', methods=['GET'])
@admin_required
def articles_cleanup_preview():
    """Show what the cleanup would do - no changes yet"""
    from models.article_barcode import ArticleBarcode
    import re

    # Find all articles ending with -N (N is 2 to 99)
    all_articles = Article.query.all()
    pattern = re.compile(r'^(.+)-(\d{1,2})$')

    to_process = []
    for art in all_articles:
        match = pattern.match(art.code_article)
        if not match:
            continue
        base_code = match.group(1)
        suffix_num = int(match.group(2))
        # Only consider suffix 2 and above (not -1)
        if suffix_num < 2:
            continue

        base_art = Article.query.filter_by(code_article=base_code).first()

        item = {
            'duplicate': art,
            'base_code': base_code,
            'base_exists': base_art is not None,
            'base_id': base_art.id if base_art else None,
            'has_receptions': len(art.lignes) > 0,
            'reception_count': len(art.lignes)
        }
        to_process.append(item)

    return render_template('admin/articles/cleanup.html',
                           items=to_process,
                           total=len(to_process))


@admin.route('/articles/cleanup/execute', methods=['POST'])
@admin_required
def articles_cleanup_execute():
    """Actually run the cleanup"""
    from models.article_barcode import ArticleBarcode
    import re

    all_articles = Article.query.all()
    pattern = re.compile(r'^(.+)-(\d{1,2})$')

    moved = 0
    deleted = 0
    kept = 0
    skipped = 0
    errors = []

    for art in all_articles:
        match = pattern.match(art.code_article)
        if not match:
            continue
        base_code = match.group(1)
        suffix_num = int(match.group(2))
        if suffix_num < 2:
            continue

        base_art = Article.query.filter_by(code_article=base_code).first()
        if not base_art:
            skipped += 1
            continue

        try:
            # Move the barcode as extra to base article
            if art.barcode:
                # Check if barcode already exists somewhere
                existing_primary = Article.query.filter_by(barcode=art.barcode).filter(Article.id != art.id).first()
                existing_extra = ArticleBarcode.query.filter_by(barcode=art.barcode).first()

                if not existing_primary and not existing_extra:
                    # Add as extra barcode to base
                    extra = ArticleBarcode(article_id=base_art.id, barcode=art.barcode)
                    db.session.add(extra)
                    # Remove barcode from duplicate to avoid conflict
                    art.barcode = None
                    db.session.flush()
                    moved += 1

            # Move extra barcodes too
            for eb in list(art.barcodes):
                existing_extra = ArticleBarcode.query.filter_by(barcode=eb.barcode).filter(ArticleBarcode.id != eb.id).first()
                if not existing_extra:
                    eb.article_id = base_art.id
                    db.session.flush()

            # Delete or keep the duplicate
            if art.lignes:
                # Has receptions - just mark inactive
                art.is_active = False
                kept += 1
            else:
                # Safe to delete
                db.session.delete(art)
                deleted += 1

        except Exception as e:
            errors.append(f'{art.code_article}: {str(e)}')
            db.session.rollback()

    db.session.commit()

    flash(f'Nettoyage termine: {moved} codes-barres deplaces, {deleted} articles supprimes, {kept} conserves (avec receptions), {skipped} ignores', 'success')
    if errors:
        for e in errors[:5]:
            flash(e, 'error')

    return redirect(url_for('admin.articles'))

@admin.route('/articles/<int:id>/barcode/add', methods=['POST'])
@admin_required
def article_barcode_add(id):
    from models.article_barcode import ArticleBarcode
    article = db.session.get(Article, id)
    if not article:
        flash('Article introuvable', 'error')
        return redirect(url_for('admin.articles'))

    new_barcode = request.form.get('new_barcode', '').strip()
    if not new_barcode:
        flash('Code-barres vide', 'error')
        return redirect(url_for('admin.article_edit', id=id))

    # Check if barcode already exists anywhere
    if Article.query.filter_by(barcode=new_barcode).first():
        flash('Ce code-barres existe deja sur un autre article', 'error')
        return redirect(url_for('admin.article_edit', id=id))

    if ArticleBarcode.query.filter_by(barcode=new_barcode).first():
        flash('Ce code-barres existe deja sur un autre article', 'error')
        return redirect(url_for('admin.article_edit', id=id))

    extra = ArticleBarcode(article_id=article.id, barcode=new_barcode)
    db.session.add(extra)
    db.session.commit()
    flash('Code-barres ajoute', 'success')
    return redirect(url_for('admin.article_edit', id=id))


@admin.route('/articles/<int:id>/barcode/<int:barcode_id>/delete', methods=['POST'])
@admin_required
def article_barcode_delete(id, barcode_id):
    from models.article_barcode import ArticleBarcode
    extra = db.session.get(ArticleBarcode, barcode_id)
    if extra and extra.article_id == id:
        db.session.delete(extra)
        db.session.commit()
        flash('Code-barres supprime', 'success')
    return redirect(url_for('admin.article_edit', id=id))

@admin.route('/articles/export')
@admin_required
def articles_export():
    """Export all active articles with all barcodes as CSV"""
    from models.article_barcode import ArticleBarcode

    articles = Article.query.filter_by(is_active=True).order_by(Article.code_article).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', lineterminator='\n')

    # Header row
    writer.writerow(['code_article', 'designation', 'barcode'])

    # One row per barcode
    for art in articles:
        all_barcodes = art.get_all_barcodes()
        if all_barcodes:
            for bc in all_barcodes:
                writer.writerow([art.code_article, art.designation, bc])
        else:
            # Article with no barcode - still export
            writer.writerow([art.code_article, art.designation, ''])

    today = date.today().strftime('%Y%m%d')
    filename = f'articles_export_{today}.csv'

    csv_bytes = output.getvalue().encode('utf-8-sig')

    response = make_response(csv_bytes)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@admin.route('/articles/import', methods=['GET', 'POST'])
@admin_required
def article_import():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Aucun fichier selectionne', 'error') 
            return render_template('admin/articles/import.html')

        filename = file.filename.lower()
        created = 0
        updated = 0
        errors  = []

        try:
            if filename.endswith('.csv'):
                raw = file.stream.read()
                for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                    try:
                        stream = io.StringIO(raw.decode(enc))
                        break
                    except Exception:
                        continue
                reader = csv.DictReader(stream, delimiter=';')
                rows = list(reader)

            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                import openpyxl
                wb = openpyxl.load_workbook(file)
                ws = wb.active
                headers = [str(cell.value).strip() if cell.value else '' for cell in ws[1]]
                rows = []
                for row in ws.iter_rows(min_row=2, values_only=True):
                    rows.append(dict(zip(headers, [str(v).strip() if v is not None else '' for v in row])))
            else:
                flash('Format non supporte. Utilisez CSV ou XLSX', 'error')
                return render_template('admin/articles/import.html')

            # Bulk fetch existing articles
            existing_codes    = {a.code_article: a for a in Article.query.all()}
            existing_barcodes = {a.barcode: a for a in Article.query.filter(Article.barcode != None).all()}

            # Also load extra barcodes
            from models.article_barcode import ArticleBarcode
            extra_barcodes = {b.barcode: b.article_id for b in ArticleBarcode.query.all()}

            new_articles = []
            # Track extra barcodes to add AFTER new articles are saved with IDs
            # Format: list of tuples (code_article, barcode)
            pending_extras_for_existing = []  # for existing articles - we have art.id
            pending_extras_for_new = []       # for new articles - need to lookup id after save

            for i, row in enumerate(rows, start=2):
                code    = (row.get('code_article', '') or '').strip().replace('\r', '').replace('\n', '')
                desig   = (row.get('designation', '') or '').strip().replace('\r', '').replace('\n', '')
                barcode = (row.get('barcode', '') or '').strip().replace('\r', '').replace('\n', '')
                unite   = ((row.get('unite', '') or 'piece').strip() or 'piece').replace('\r', '').replace('\n', '')

                if not code or not desig or not barcode:
                    errors.append(f'Ligne {i}: barcode, code_article et designation sont obligatoires')
                    continue

                if code in existing_codes:
                    art = existing_codes[code]

                    # Check if it's a new article (in memory) or existing (in DB)
                    if art.id is None:
                        # New article added earlier in this import - add extra barcode later
                        if barcode not in existing_barcodes and barcode not in extra_barcodes:
                            pending_extras_for_new.append((code, barcode))
                            extra_barcodes[barcode] = -1  # placeholder to mark as reserved
                        else:
                            errors.append(f'Ligne {i}: barcode {barcode} deja utilise par un autre article')
                        updated += 1
                    else:
                        # Existing article in DB - update fields
                        art.designation = desig
                        art.unite = unite

                        # Check if barcode is new for this article
                        art_barcodes = [art.barcode] + [b.barcode for b in art.barcodes]
                        if barcode not in art_barcodes:
                            if barcode not in existing_barcodes and barcode not in extra_barcodes:
                                pending_extras_for_existing.append(
                                    ArticleBarcode(article_id=art.id, barcode=barcode)
                                )
                                extra_barcodes[barcode] = art.id
                            else:
                                errors.append(f'Ligne {i}: barcode {barcode} deja utilise par un autre article')
                        updated += 1

                elif barcode in existing_barcodes or barcode in extra_barcodes:
                    errors.append(f'Ligne {i}: barcode {barcode} deja utilise par un autre article')

                else:
                    # New article (first time seen)
                    new_art = Article(
                        code_article=code,
                        designation=desig,
                        barcode=barcode,
                        unite=unite
                    )
                    new_articles.append(new_art)
                    existing_codes[code]       = new_art
                    existing_barcodes[barcode] = new_art
                    created += 1

            # STEP 1: Save all new articles first, then commit to get IDs
            if new_articles:
                for a in new_articles:
                    db.session.add(a)
                db.session.flush()  # assign IDs but don't commit yet

            # STEP 2: Save extra barcodes for existing articles
            if pending_extras_for_existing:
                for eb in pending_extras_for_existing:
                    db.session.add(eb)

            # STEP 3: Save extra barcodes for new articles (now they have IDs)
            if pending_extras_for_new:
                # Refresh existing_codes to get the saved new articles with IDs
                saved_new = {a.code_article: a for a in new_articles}
                for code, barcode in pending_extras_for_new:
                    art = saved_new.get(code)
                    if art and art.id:
                        eb = ArticleBarcode(article_id=art.id, barcode=barcode)
                        db.session.add(eb)

            db.session.commit()
            flash(f'Import termine: {created} crees, {updated} mis a jour, {len(errors)} erreurs', 'success')
            if errors:
                for e in errors[:5]:
                    flash(e, 'error')

        except Exception as ex:
            flash(f'Erreur lors de limport: {str(ex)}', 'error')

        return redirect(url_for('admin.articles'))

    return render_template('admin/articles/import.html')


# --- FOURNISSEURS ----------------------------------------

@admin.route('/fournisseurs')
@admin_required
def fournisseurs():
    all_fournisseurs = Fournisseur.query.order_by(Fournisseur.nom).all()
    return render_template('admin/fournisseurs/list.html', fournisseurs=all_fournisseurs)


@admin.route('/fournisseurs/new', methods=['GET', 'POST'])
@admin_required
def fournisseur_new():
    if request.method == 'POST':
        nom       = request.form.get('nom', '').strip()
        contact   = request.form.get('contact', '').strip()
        telephone = request.form.get('telephone', '').strip()

        if not nom:
            flash('Le nom est obligatoire', 'error')
            return render_template('admin/fournisseurs/form.html', fournisseur=None)

        f = Fournisseur(nom=nom, contact=contact, telephone=telephone)
        db.session.add(f)
        db.session.commit()
        flash('Fournisseur cree', 'success')
        return redirect(url_for('admin.fournisseurs'))

    return render_template('admin/fournisseurs/form.html', fournisseur=None)


@admin.route('/fournisseurs/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def fournisseur_edit(id):
    f = db.session.get(Fournisseur, id)
    if not f:
        flash('Fournisseur introuvable', 'error')
        return redirect(url_for('admin.fournisseurs'))

    if request.method == 'POST':
        f.nom       = request.form.get('nom', '').strip()
        f.contact   = request.form.get('contact', '').strip()
        f.telephone = request.form.get('telephone', '').strip()
        db.session.commit()
        flash('Fournisseur mis a jour', 'success')
        return redirect(url_for('admin.fournisseurs'))

    return render_template('admin/fournisseurs/form.html', fournisseur=f)


@admin.route('/fournisseurs/<int:id>/toggle', methods=['POST'])
@admin_required
def fournisseur_toggle(id):
    f = db.session.get(Fournisseur, id)
    if f:
        f.is_active = not f.is_active
        db.session.commit()
    return redirect(url_for('admin.fournisseurs'))


# --- RECEPTIONS ------------------------------------------

@admin.route('/receptions')
@admin_required
def receptions():
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    query = Reception.query

    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Reception.date_reception >= df)
        except:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Reception.date_reception <= dt)
        except:
            pass

    receptions = query.order_by(Reception.created_at.desc()).all()
    return render_template('admin/receptions/list.html',
                           receptions=receptions,
                           date_from=date_from,
                           date_to=date_to)


@admin.route('/receptions/<int:id>')
@admin_required
def reception_detail(id):
    reception = db.session.get(Reception, id)
    if not reception:
        flash('Reception introuvable', 'error')
        return redirect(url_for('admin.receptions'))
    return render_template('admin/receptions/detail.html', reception=reception)

@admin.route('/receptions/<int:id>/ligne/<int:ligne_id>/edit', methods=['POST'])
@admin_required
def reception_ligne_edit(id, ligne_id):
    """Edit qty of an existing ligne in a finished reception"""
    reception = db.session.get(Reception, id)
    if not reception:
        flash('Reception introuvable', 'error')
        return redirect(url_for('admin.receptions'))
    if reception.statut != 'terminee':
        flash('Modification uniquement pour receptions terminees', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    ligne = db.session.get(ReceptionLigne, ligne_id)
    if not ligne or ligne.reception_id != id:
        flash('Ligne introuvable', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    new_qte_raw = request.form.get('qte', '').strip()
    try:
        new_qte = float(new_qte_raw)
    except ValueError:
        flash('Quantite invalide', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    if new_qte < 0:
        flash('Quantite ne peut pas etre negative', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    old_qte = ligne.qte_recue
    ligne.qte_recue = new_qte
    db.session.commit()
    flash(f'Quantite mise a jour: {old_qte} -> {new_qte}', 'success')
    return redirect(url_for('admin.reception_detail', id=id))


@admin.route('/receptions/<int:id>/ligne/<int:ligne_id>/delete', methods=['POST'])
@admin_required
def reception_ligne_delete(id, ligne_id):
    """Delete a ligne from a finished reception"""
    reception = db.session.get(Reception, id)
    if not reception:
        flash('Reception introuvable', 'error')
        return redirect(url_for('admin.receptions'))
    if reception.statut != 'terminee':
        flash('Suppression uniquement pour receptions terminees', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    ligne = db.session.get(ReceptionLigne, ligne_id)
    if not ligne or ligne.reception_id != id:
        flash('Ligne introuvable', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    db.session.delete(ligne)
    db.session.commit()
    flash('Ligne supprimee', 'success')
    return redirect(url_for('admin.reception_detail', id=id))


@admin.route('/receptions/<int:id>/ligne/add', methods=['POST'])
@admin_required
def reception_ligne_add(id):
    """Add a new article to a finished reception"""
    from models.article_barcode import ArticleBarcode
    reception = db.session.get(Reception, id)
    if not reception:
        flash('Reception introuvable', 'error')
        return redirect(url_for('admin.receptions'))
    if reception.statut != 'terminee':
        flash('Ajout uniquement pour receptions terminees', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    search = request.form.get('article_search', '').strip()
    qte_raw = request.form.get('qte', '').strip()

    if not search or not qte_raw:
        flash('Article et quantite obligatoires', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    try:
        qte = float(qte_raw)
    except ValueError:
        flash('Quantite invalide', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    if qte < 0:
        flash('Quantite ne peut pas etre negative', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    # Search by code_article first
    article = Article.query.filter_by(code_article=search).first()

    # Then by primary barcode
    if not article:
        article = Article.query.filter_by(barcode=search).first()

    # Then by extra barcode
    if not article:
        extra = ArticleBarcode.query.filter_by(barcode=search).first()
        if extra:
            article = db.session.get(Article, extra.article_id)

    if not article:
        flash(f'Article introuvable: {search}', 'error')
        return redirect(url_for('admin.reception_detail', id=id))

    # Check if already exists in reception
    existing = ReceptionLigne.query.filter_by(
        reception_id=id,
        article_id=article.id
    ).first()

    if existing:
        existing.qte_recue = qte
        flash(f'Article deja present - Qte remplacee: {qte}', 'success')
    else:
        ligne = ReceptionLigne(
            reception_id=id,
            article_id=article.id,
            qte_recue=qte
        )
        db.session.add(ligne)
        flash(f'Article ajoute: {article.designation} - {qte}', 'success')

    db.session.commit()
    return redirect(url_for('admin.reception_detail', id=id))

@admin.route('/receptions/<int:id>/delete', methods=['POST'])
@admin_required
def reception_delete(id):
    reception = db.session.get(Reception, id)
    if reception:
        db.session.delete(reception)
        db.session.commit()
        flash('Reception supprimee', 'success')
    return redirect(url_for('admin.receptions'))

# --- INVENTAIRES -----------------------------------------

@admin.route('/inventaires')
@admin_required
def inventaires():
    from models.inventaire import Inventaire
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    query = Inventaire.query

    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Inventaire.date_inventaire >= df)
        except:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Inventaire.date_inventaire <= dt)
        except:
            pass

    inventaires_list = query.order_by(Inventaire.created_at.desc()).all()
    return render_template('admin/inventaires/list.html',
                           inventaires=inventaires_list,
                           date_from=date_from,
                           date_to=date_to)


@admin.route('/inventaires/<int:id>')
@admin_required
def inventaire_detail(id):
    from models.inventaire import Inventaire
    inventaire = db.session.get(Inventaire, id)
    if not inventaire:
        flash('Inventaire introuvable', 'error')
        return redirect(url_for('admin.inventaires'))
    return render_template('admin/inventaires/detail.html', inventaire=inventaire)


@admin.route('/inventaires/<int:id>/delete', methods=['POST'])
@admin_required
def inventaire_delete(id):
    from models.inventaire import Inventaire
    inventaire = db.session.get(Inventaire, id)
    if inventaire:
        db.session.delete(inventaire)
        db.session.commit()
        flash('Inventaire supprime', 'success')
    return redirect(url_for('admin.inventaires'))


@admin.route('/inventaires/<int:id>/export')
@admin_required
def inventaire_export(id):
    from models.inventaire import Inventaire
    inventaire = db.session.get(Inventaire, id)
    if not inventaire:
        flash('Inventaire introuvable', 'error')
        return redirect(url_for('admin.inventaires'))

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', lineterminator='\n')

    for ligne in inventaire.lignes:
        barcode = (ligne.article.barcode or '').strip() if ligne.article else ''
        qte = ligne.qte_physique
        if barcode:
            writer.writerow([barcode, qte])

    csv_bytes = output.getvalue().encode('cp1252', errors='replace')
    response = make_response(csv_bytes)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=' + inventaire.reference + '.csv'
    return response


@admin.route('/inventaires/export')
@admin_required
def inventaires_export_all():
    from models.inventaire import Inventaire
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    query = Inventaire.query

    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Inventaire.date_inventaire >= df)
        except:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Inventaire.date_inventaire <= dt)
        except:
            pass

    inventaires_list = query.order_by(Inventaire.date_inventaire.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', lineterminator='\n')

    for inv in inventaires_list:
        for ligne in inv.lignes:
            barcode = (ligne.article.barcode or '').strip() if ligne.article else ''
            qte = ligne.qte_physique
            if barcode:
                writer.writerow([barcode, qte])

    today = date.today().strftime('%Y%m%d')
    csv_bytes = output.getvalue().encode('cp1252', errors='replace')
    response = make_response(csv_bytes)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=inventaires_export_' + today + '.csv'
    return response

# --- EXPORT CSV ------------------------------------------

@admin.route('/export')
@admin_required
def export():
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    query = Reception.query

    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Reception.date_reception >= df)
        except:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Reception.date_reception <= dt)
        except:
            pass

    receptions = query.order_by(Reception.date_reception.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', lineterminator='\n')

    for rec in receptions:
        for ligne in rec.lignes:
            barcode = (ligne.article.barcode or '').strip() if ligne.article else ''
            qte = ligne.qte_recue
            if barcode:
                writer.writerow([barcode, qte])

    today = date.today().strftime('%Y%m%d')
    filename = f'pda_export_{today}.csv'

    csv_text = output.getvalue()
    csv_bytes = csv_text.encode('cp1252', errors='replace')

    response = make_response(csv_bytes)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response



@admin.route('/receptions/<int:id>/export')
@admin_required
def reception_export(id):
    reception = db.session.get(Reception, id)
    if not reception:
        flash('Reception introuvable', 'error')
        return redirect(url_for('admin.receptions'))
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', lineterminator='\n')
    for ligne in reception.lignes:
        barcode = (ligne.article.barcode or '').strip() if ligne.article else ''
        qte = ligne.qte_recue
        if barcode:
            writer.writerow([barcode, qte])
    csv_bytes = output.getvalue().encode('cp1252', errors='replace')
    response = make_response(csv_bytes)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=' + reception.reference + '.csv'
    return response

