from flask import Flask, send_from_directory
from config import Config
from extensions import db, login_manager
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from routes.main import main
    from routes.scan import scan
    from routes.admin import admin
    from routes.api import api
    from routes.verify import verify

    app.register_blueprint(main)
    app.register_blueprint(scan)
    app.register_blueprint(admin)
    app.register_blueprint(api)
    app.register_blueprint(verify)

    @app.route('/manifest.json')
    def manifest():
        return send_from_directory('static', 'manifest.json')

    @app.route('/sw.js')
    def sw():
        return send_from_directory('static', 'sw.js', mimetype='application/javascript')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory('static/icons', 'icon-192.png')

    @app.after_request
    def set_security_headers(response):
        response.headers['Permissions-Policy'] = 'camera=*, microphone=*'
        return response

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    with app.app_context():
        from models.article import Article
        from models.article_barcode import ArticleBarcode
        from models.fournisseur import Fournisseur
        from models.reception import Reception, ReceptionLigne
        from models.user import User
        from models.stock_level import StockLevel
        from models.inventaire import Inventaire, InventaireLigne
        db.create_all()
        seed_admin()

    return app


def seed_admin():
    from models.user import User
    from extensions import db
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User()
        admin.username = 'admin'
        admin.full_name = 'Administrateur'
        admin.role = 'admin'
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


app = create_app()

if __name__ == '__main__':
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    ssl_cert = os.environ.get('SSL_CERT_PATH')
    ssl_key = os.environ.get('SSL_KEY_PATH')
    if ssl_cert and ssl_key:
        ssl_context = (ssl_cert, ssl_key)
    elif debug:
        ssl_context = 'adhoc'
    else:
        ssl_context = None
    app.run(host=host, port=port, debug=debug, ssl_context=ssl_context)
