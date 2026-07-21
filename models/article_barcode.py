from extensions import db
from datetime import datetime

class ArticleBarcode(db.Model):
    __tablename__ = 'article_barcodes'

    id         = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    barcode    = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ArticleBarcode {self.barcode}>'