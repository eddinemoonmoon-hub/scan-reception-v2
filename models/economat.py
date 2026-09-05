from extensions import db
from datetime import datetime

class EconomatStock(db.Model):
    __tablename__ = 'economat_stock'

    id         = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False, unique=True)
    quantity   = db.Column(db.Float, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    article = db.relationship('Article', lazy=True)


class EconomatDocument(db.Model):
    __tablename__ = 'economat_documents'

    id            = db.Column(db.Integer, primary_key=True)
    reference     = db.Column(db.String(50), unique=True, nullable=False)
    doc_type      = db.Column(db.String(20), nullable=False)  # 'entree' or 'sortie'
    agent_name    = db.Column(db.String(100), nullable=False)
    date_document = db.Column(db.Date, default=datetime.utcnow)
    statut        = db.Column(db.String(20), default='en_cours')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    lignes = db.relationship('EconomatLigne', backref='document', lazy=True, cascade='all, delete-orphan')

    @property
    def total_lignes(self):
        return len(self.lignes)

    @staticmethod
    def generate_reference(doc_type):
        import random
        now = datetime.utcnow()
        prefix = 'ENT' if doc_type == 'entree' else 'SOR'
        while True:
            ref = f"{prefix}-{now.year}{now.month:02d}-{random.randint(1000, 9999)}"
            if not EconomatDocument.query.filter_by(reference=ref).first():
                return ref


class EconomatLigne(db.Model):
    __tablename__ = 'economat_lignes'

    id          = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('economat_documents.id'), nullable=False)
    article_id  = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    qte         = db.Column(db.Float, nullable=False, default=1)
    scanned_at  = db.Column(db.DateTime, default=datetime.utcnow)

    article = db.relationship('Article', lazy=True)