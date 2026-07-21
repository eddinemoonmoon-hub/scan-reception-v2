from extensions import db
from datetime import datetime

class Reception(db.Model):
    __tablename__ = 'receptions'

    id             = db.Column(db.Integer, primary_key=True)
    reference      = db.Column(db.String(50), unique=True, nullable=False)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    date_reception = db.Column(db.Date, default=datetime.utcnow)
    notes          = db.Column(db.Text, nullable=True)
    statut         = db.Column(db.String(20), default='en_cours')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    lignes = db.relationship(
        'ReceptionLigne',
        backref='reception',
        lazy=True,
        cascade='all, delete-orphan'
    )

    @staticmethod
    def generate_reference():
        import random
        now = datetime.utcnow()
        while True:
            ref = f"REC-{now.year}{now.month:02d}-{random.randint(1000, 9999)}"
            if not Reception.query.filter_by(reference=ref).first():
                return ref

    @property
    def total_lignes(self):
        return len(self.lignes)

    @property
    def total_quantite(self):
        return sum(l.qte_recue for l in self.lignes)

    def __repr__(self):
        return f'<Reception {self.reference}>'


class ReceptionLigne(db.Model):
    __tablename__ = 'reception_lignes'

    id           = db.Column(db.Integer, primary_key=True)
    reception_id = db.Column(db.Integer, db.ForeignKey('receptions.id'), nullable=False)
    article_id   = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    qte_recue    = db.Column(db.Float, nullable=False, default=1)
    notes        = db.Column(db.String(200), nullable=True)
    scanned_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Ligne rec:{self.reception_id} art:{self.article_id} x{self.qte_recue}>'

