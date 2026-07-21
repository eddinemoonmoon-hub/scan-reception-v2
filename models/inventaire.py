from extensions import db
from datetime import datetime

class Inventaire(db.Model):
    __tablename__ = 'inventaires'

    id              = db.Column(db.Integer, primary_key=True)
    reference       = db.Column(db.String(50), unique=True, nullable=False)
    warehouse_code  = db.Column(db.String(10), default='20')
    agent_name      = db.Column(db.String(100), nullable=True)
    date_inventaire = db.Column(db.Date, default=datetime.utcnow)
    notes           = db.Column(db.Text, nullable=True)
    statut          = db.Column(db.String(20), default='en_cours')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    lignes = db.relationship('InventaireLigne', backref='inventaire', lazy=True, cascade='all, delete-orphan')

    @property
    def total_lignes(self):
        return len(self.lignes)

    @property
    def total_ecarts(self):
        return sum(1 for l in self.lignes if l.ecart != 0)

    @staticmethod
    def generate_reference():
        import random
        now = datetime.utcnow()
        while True:
            ref = f"INV-{now.year}{now.month:02d}-{random.randint(1000, 9999)}"
            if not Inventaire.query.filter_by(reference=ref).first():
                return ref


class InventaireLigne(db.Model):
    __tablename__ = 'inventaire_lignes'

    id             = db.Column(db.Integer, primary_key=True)
    inventaire_id  = db.Column(db.Integer, db.ForeignKey('inventaires.id'), nullable=False)
    article_id     = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    qte_systeme    = db.Column(db.Float, nullable=False, default=0)
    qte_physique   = db.Column(db.Float, nullable=False, default=0)
    ecart          = db.Column(db.Float, nullable=False, default=0)
    scanned_at     = db.Column(db.DateTime, default=datetime.utcnow)

    article = db.relationship('Article', lazy=True)