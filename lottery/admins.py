from flask import Blueprint, jsonify, request
from .auth import loginRequired
from .db import User, dbSession
from .config import USER_ROLE, USER_STATUS
from .common import getDictKeyByValue, logInfo
from .auth import getUserIdFromSession


bp = Blueprint('admins', __name__)


@bp.route('/admins/profile', methods=['GET'])
@loginRequired(USER_ROLE['admin'])
def getProfile():

    user = User.query.get(getUserIdFromSession())

    if user is None:
        logInfo('user not found the from session')
        return jsonify({'error': 'user_not_found'}), 404


    profileData = {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'surname': user.surname,
        'phone': user.phone,
        'age': user.age,
        'role': getDictKeyByValue(USER_ROLE, user.role),
        'status': getDictKeyByValue(USER_STATUS, user.status)
    }

    return jsonify(profileData)