from flask import Blueprint, jsonify
from flask_jwt_extended import (
    JWTManager,
    verify_jwt_in_request,
    get_jwt_identity,
    get_jwt_claims,
    get_raw_jwt
)
from functools import wraps
from .db import db


bp = Blueprint('auth', __name__)
jwt = JWTManager()


class RevokedTokenAdmin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)


@jwt.user_claims_loader
def addClaimsToAccessToken(user):
    return {'role': user.role}


@jwt.user_identity_loader
def userIdentityLookup(user):
    return user.id


@jwt.token_in_blacklist_loader
def checkTokenInBlacklist(decrypted_token):
    jti = decrypted_token['jti']
    return RevokedTokenAdmin.is_jti_blacklisted(jti)


def getSessionId():

    jwt = get_raw_jwt()

    if 'jti' in jwt:
        return jwt['jti']
    return None


def getAdminIdFromSession():
    try:
        userId = get_jwt_identity()
    except:
        return None

    return userId


def loginRequired(accessLevel):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            try:
                verify_jwt_in_request()
            except:
                return jsonify({'error': 'You do not have access to requested resource'}), 403

            claims = get_jwt_claims()

            if claims['role'] < accessLevel:
                return jsonify({'error': 'You do not have access to requested resource'}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def getUserIdFromSession():
    try:
        userId = get_jwt_identity()
    except:
        return None

    return userId

