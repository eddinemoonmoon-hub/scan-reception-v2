from extensions import db
from datetime import datetime

class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'

    id         = db.Column(db.Integer, primary_key=True)
    nom        = db.Column(db.String(150), nullable=False)
    contact    = db.Column(db.String(100), nullable=True)
    telephone  = db.Column(db.String(30), nullable=True)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    receptions = db.relationship('Reception', backref='fournisseur', lazy=True)

    def __repr__(self):
        return f'<Fournisseur {self.nom}>'
