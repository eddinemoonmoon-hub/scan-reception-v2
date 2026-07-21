from extensions import db
from datetime import datetime

class StockLevel(db.Model):
    __tablename__ = 'stock_levels'

    id             = db.Column(db.Integer, primary_key=True)
    article_code   = db.Column(db.String(50), nullable=False, index=True)
    warehouse_code = db.Column(db.String(10), nullable=False, default='20')
    quantity       = db.Column(db.Float, nullable=False, default=0)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('article_code', 'warehouse_code', name='uq_stock_article_warehouse'),
    )