from extensions import db
from datetime import datetime

class Article(db.Model):
    __tablename__ = 'articles'

    id           = db.Column(db.Integer, primary_key=True)
    code_article = db.Column(db.String(50), unique=True, nullable=False)
    designation  = db.Column(db.String(200), nullable=False)
    barcode      = db.Column(db.String(100), unique=True, nullable=True)
    unite        = db.Column(db.String(20), default='piece')
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    lignes   = db.relationship('ReceptionLigne', backref='article', lazy=True)
    barcodes = db.relationship('ArticleBarcode', backref='article', lazy=True,
                               cascade='all, delete-orphan')

    def get_all_barcodes(self):
        """Returns all barcodes for this article including primary"""
        all_barcodes = []
        if self.barcode:
            all_barcodes.append(self.barcode)
        for b in self.barcodes:
            if b.barcode not in all_barcodes:
                all_barcodes.append(b.barcode)
        return all_barcodes

    def __repr__(self):
        return f'<Article {self.code_article} - {self.designation}>'