from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contracts = db.relationship('Contract', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f"<User {self.username}>"

class Contract(db.Model):
    __tablename__ = 'contract'
    id = db.Column(db.Integer, primary_key=True)
    contract_date = db.Column(db.DateTime, default=datetime.utcnow)
    contract_number = db.Column(db.String(128), unique=False, nullable=False)
    contractor = db.Column(db.String(256))
    main_or_additional = db.Column(db.String(64), default="Основной договор")
    payment_type = db.Column(db.String(64))
    amount_total = db.Column(db.Float, default=0.0)
    amount_paid = db.Column(db.Float, default=0.0)
    amount_earned = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(64), default="в работе")
    archived = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    parent_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=True)
    extra_type = db.Column(db.String(32), nullable=True)
    extra_amount = db.Column(db.Float, nullable=True)

    parent = db.relationship('Contract', remote_side=[id], backref=db.backref('subcontracts', cascade='all, delete-orphan', lazy='dynamic'))

    def __repr__(self):
        return f"<Contract {self.contract_number}>"

class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(512))
    unit = db.Column(db.String(64))
    quantity = db.Column(db.Float, default=0.0)
    price_per_unit = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)

    contract = db.relationship('Contract', backref=db.backref('services', cascade='all, delete-orphan', lazy='dynamic'))

class ExtraService(db.Model):
    __tablename__ = 'extra_service'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(512))
    price = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)

    contract = db.relationship('Contract', backref=db.backref('extra_services', cascade='all, delete-orphan', lazy='dynamic'))

class ContractHistory(db.Model):
    __tablename__ = 'contract_history'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    action = db.Column(db.String(1024))
    actor = db.Column(db.String(128))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    contract = db.relationship('Contract', backref=db.backref('history', order_by=date.desc(), lazy='dynamic'))