from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .config import USER_STATUS, USER_ROLE, PRIZE_TYPE, CODE_STATUS, PRIZE_REQUEST_STATUS

db = SQLAlchemy()
dbSession = db.session


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=True, unique=True)
    name = db.Column(db.String(50), default='')
    surname = db.Column(db.String(50), default='')
    phone = db.Column(db.String(50), default='')
    age = db.Column(db.SmallInteger)
    password = db.Column(db.String(255), nullable=True)
    status = db.Column(db.SmallInteger, default=USER_STATUS['created'])
    role = db.Column(db.SmallInteger, default=USER_ROLE['user'])
    created = db.Column(db.DateTime, default=datetime.utcnow)
    passwordResetRequestedAt = db.Column(db.DateTime, nullable=True)
    sticksCount = db.Column(db.Integer, default=0)


class Cheque(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    userId = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    number = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(255), nullable=True)


class Stick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(255), nullable=True)


class Code(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    userId = db.Column(db.Integer, nullable=True)
    status = db.Column(db.SmallInteger, default=CODE_STATUS['not_used'])


class PrizeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.SmallInteger, default=PRIZE_REQUEST_STATUS['active'])
    plNumbers = db.Column(db.String(255), nullable=True)


class PrizeRequestDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prizeRequestId = db.Column(db.Integer, db.ForeignKey('prize_request.id'), nullable=False)
    type = db.Column(db.SmallInteger, default=PRIZE_TYPE['small'])
    count = db.Column(db.Integer, nullable=False)


class Prize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.SmallInteger, default=PRIZE_TYPE['small'])
    sticksNeeded = db.Column(db.SmallInteger, default=PRIZE_TYPE['small'])
    count = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, default=0)