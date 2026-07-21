from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import hashlib

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    full_name  = db.Column(db.String(150), nullable=True)
    role       = db.Column(db.String(20), default='admin')
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password == hashlib.sha256(password.encode()).hexdigest()

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
