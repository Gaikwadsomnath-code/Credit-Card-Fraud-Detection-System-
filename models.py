from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from extensions import db
from sqlalchemy.sql import func

#db = SQLAlchemy()


#  User Table
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default='admin')  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cards = db.relationship('Card', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    


#  Card Table
class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_number = db.Column(db.String(20), nullable=False)  # Masked or encrypted
    bank_name = db.Column(db.String(50), nullable=False)
    card_type = db.Column(db.String(20))  # e.g., Visa, MasterCard
    status = db.Column(db.String(20), default='active')  # active/blocked

    transactions = db.relationship('Transaction', backref='card', lazy=True)


#  Transaction Table

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'))
    amount = db.Column(db.Float)
    merchant_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())  # डेटाबेस लेव्हल default
    fraud_predicted = db.Column(db.Boolean)
    fraud_score = db.Column(db.Float, nullable=True)
    flag_reason = db.Column(db.String(255), nullable=True)
    batch_id = db.Column(db.String(100), nullable=False)
    is_prediction = db.Column(db.Boolean, default=False)
    is_fraud = db.Column(db.Boolean, default=False)





#  Fraud Alert Table
class FraudAlert(db.Model):
    __tablename__ = 'fraud_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    confirmed_by_user = db.Column(db.Boolean, default=None)  # None = not confirmed yet
    action_taken = db.Column(db.String(50))  # Blocked, ignored, alerted
    alert_time = db.Column(db.DateTime, default=datetime.utcnow)  # Created at
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  #  Auto update on change

    #  Relationship to Transaction
    transaction = db.relationship('Transaction', backref='fraud_alerts', lazy=True)

