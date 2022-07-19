import multiprocessing
import random

import bcrypt
from flask import Blueprint, jsonify, request
from .auth import loginRequired
from .db import User, dbSession, db, Cheque, PrizeRequest, PrizeRequestDetails, Prize
from .config import USER_ROLE, USER_STATUS, JWT_EXPIRATION_TIME, CRYPTO_TOKEN_EXPIRATION, \
    EMAIL_CONFIRMATION_URL, CLIENT_BASE_URL, RESET_PASSWORD_URL, ITEMS_PER_PAGE, PRIZE_TYPE
from .common import getDictKeyByValue, logInfo, decrypt, encrypt, sendEmail, logError
from .auth import getUserIdFromSession
from .validation_schemas.users_schemas import UsersSchemas
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from flask_babel import gettext

bp = Blueprint('users', __name__)

@bp.route('/users/profile', methods=['GET'])
@loginRequired(USER_ROLE['user'])
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
        'status': getDictKeyByValue(USER_STATUS, user.status),
        'sticksCount': user.sticksCount
    }

    return jsonify(profileData)


@bp.route('/users/email/confirm', methods=['POST'])
def confirmEmail():

    requestData = request.json

    validation_result = UsersSchemas.validateConfirmEmail(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    if not decrypt(requestData['token']):
        logInfo('not able to decrypt token')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    token = decrypt(requestData['token']).split(';')

    if token[0] == '':
        try:
            token[0] = int(token[0])
        except:
            return jsonify({'error': 'wrong_data_supplied'}), 400

    user = User.query.filter_by(
        id=token[0],
        status=USER_STATUS['created']
    ).first()

    if not user or token[1] != user.email:
        logInfo('email not provided in the token')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    if float(token[(len(token) - 1)]) < datetime.utcnow().timestamp():
        logInfo('token expired')
        return jsonify({'error': 'token_expired'}), 400

    user.status = USER_STATUS['confirmed']

    dbSession.add(user)
    dbSession.commit()

    accessToken = create_access_token(identity=user, expires_delta=timedelta(days=JWT_EXPIRATION_TIME))

    return jsonify(accessToken=accessToken, email=user.email, role=getDictKeyByValue(USER_ROLE, user.role))


@bp.route('/users/email/verification', methods=['POST'])
def requestEmailVerificationLink():

    requestData = request.json

    validation_result = UsersSchemas.validateEmailVerification(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    user = User.query.filter_by(email=requestData['email']).first()

    if user is None:
        logInfo('user with provided email not found; email={}'.format(requestData['email']))
        return jsonify({'error': 'not_existing_user'}), 400

    if user.status != USER_STATUS['created']:
        logInfo('email already confirmed; user_id={}'.format(user.id))
        return jsonify({'error': 'email_already_confirmed'}), 400

    token = str(user.id) + ';' + user.email + ';' + str(datetime.utcnow().timestamp() + CRYPTO_TOKEN_EXPIRATION)

    from . import app
    with app.app_context():
        emailConfirmationLink = app.config['BASE_URL'] + EMAIL_CONFIRMATION_URL + encrypt(token)

    thread = multiprocessing.Process(target=sendEmail, args=(
        user.email,
        gettext('signup_email_subject'),
        gettext('signup_verification_email_text_first') + '<br /><br />' +
        gettext('signup_verification_email_text_second') + '<br /><br />' +
        gettext('signup_verification_email_text_third') + '<br /><br />' +

        '<br /><br /><table width="100%" border="0" cellspacing="0" cellpadding="0"> <tr> <td> <div> <!--[if mso]> '
        '<v:roundrect xmlns_v="urn:schemas-microsoft-com:vml" xmlns_w="urn:schemas-microsoft-com:office:word" href="' +
        emailConfirmationLink +
        '" style="height:36px;v-text-anchor:middle;width:150px;" arcsize="5%" strokecolor="#199DDF" fillcolor="#EB7035"> <w:anchorlock/> '
        '<center style="color:#ffffff;font-family:Helvetica, Arial,sans-serif;font-size:16px;">' +
        gettext('signup_verification_email_welcome_button') +
        '</center> </v:roundrect> <![endif]--> <a href="'
        + emailConfirmationLink +
        '" style="background-color:#199DDF;border:1px solid #199DDF;border-radius:3px;color:#ffffff;display:inline-block;font-family:sans-serif;'
        'font-size:16px;line-height:44px;text-align:center;text-decoration:none;width:150px;-webkit-text-size-adjust:none;mso-hide:all;">' +
        gettext('signup_verification_email_welcome_button') +
        '</a> </div> </td> </tr> </table><br /><br />'
        '<a href="' + emailConfirmationLink + '">' + emailConfirmationLink + '</a></p><br /><br />'
    ))

    thread.start()

    return jsonify({'message': 'ok'})


@bp.route('/users/password/reset/request', methods=['POST'])
def passwordResetRequest():

    requestData = request.json

    validation_result = UsersSchemas.validatePasswordResetRequest(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    user = User.query.filter_by(email=requestData['email']).first()

    if user is None:
        logInfo('user not found')
        return jsonify({'error': 'wrong_email'}), 400

    if user.status != USER_STATUS['confirmed']:
        logInfo('user email not confirmed; user_id={}'.format(user.id))
        return jsonify({'error': 'email_not_confirmed'}), 400

    currentDateTime = datetime.utcnow()
    tokenGenerationTime = str(currentDateTime.timestamp())
    tokenStr = str(user.id) + ';' + user.email + ';' + tokenGenerationTime
    token = encrypt(tokenStr)

    user.passwordResetRequestedAt = currentDateTime

    dbSession.add(user)
    dbSession.commit()

    resetPasswordLink = CLIENT_BASE_URL + RESET_PASSWORD_URL + '/' + token

    thread = multiprocessing.Process(target=sendEmail, args=(
        user.email,
         gettext('password_reset_request_subject'),
        '<strong>' + gettext('password_reset_request_subject_text_first') + '</strong><br /><br />' +
        '<strong>' + gettext('password_reset_request_subject_text_second').format(resetPasswordLink) + '</strong><br /><br />'
    ))
    thread.start()

    return jsonify({'message': 'ok'})


@bp.route('/users/password/reset', methods=['POST'])
def passwordReset():

    requestData = request.json

    validation_result = UsersSchemas.validatePasswordReset(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    token = decrypt(requestData['token'])

    if not token:
        logInfo('not able to decrypt token')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    tokenValueList = token.split(";")

    if not isinstance(tokenValueList, list) or len(tokenValueList) != 3:
        logInfo('not valid amount of params in token provided')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    user = User.query.filter_by(id=tokenValueList[0]).first()

    if user is None or (user.status != USER_STATUS['confirmed']) or (user.email != tokenValueList[1]) or \
            user.passwordResetRequestedAt is None:
        logInfo('user not valid or mismatch with the token values')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    if user.passwordResetRequestedAt.timestamp() != float(tokenValueList[2]):
        logInfo('token expired; user_id={}'.format(user.id))
        return jsonify({'error': 'token_expired'}), 400

    if bcrypt.checkpw(requestData['password'].encode('utf8'), user.password):
        logInfo('previously used password; user_id={}'.format(user.id))
        return jsonify({'error': 'previously_used_password'}), 400

    user.password = bcrypt.hashpw(requestData['password'].encode('utf-8'), bcrypt.gensalt(rounds=12))
    user.passwordResetRequestedAt = None

    dbSession.add(user)
    dbSession.commit()

    thread = multiprocessing.Process(target=sendEmail, args=(
        user.email,
        gettext('password_reset_success_subject'),
        '<strong>' + gettext('password_reset_success_email_text_first') + '</strong><br /><br />' +
        '<strong>' + gettext('password_reset_success_email_text_second')+ '</strong><br /><br />'
     ))
    thread.start()

    return jsonify({'message': 'ok'})


@bp.route('/users/password/change', methods=['POST'])
@loginRequired(USER_ROLE['user'])
def passwordChange():

    requestData = request.json

    validation_result = UsersSchemas.validatePasswordChange(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    user = User.query.get(getUserIdFromSession())

    if user is None or user.status != USER_STATUS['confirmed']:
        logInfo('user not valid or mismatch with the token values')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    if not bcrypt.checkpw(requestData['password'].encode('utf8'), user.password):
        return jsonify({'error': 'incorrect_password'}), 400

    if bcrypt.checkpw(requestData['newPassword'].encode('utf8'), user.password):
        logInfo('previously used password; user_id={}'.format(user.id))
        return jsonify({'error': 'previously_used_password'}), 400

    user.password = bcrypt.hashpw(requestData['newPassword'].encode('utf-8'), bcrypt.gensalt(rounds=12))
    user.passwordResetRequestedAt = None

    dbSession.add(user)
    dbSession.commit()

    return jsonify({'message': 'ok'})


@bp.route('/users/password/reset/validate', methods=['POST'])
def validatePasswordResetToken():

    requestData = request.json

    validation_result = UsersSchemas.validatePasswordResetToken(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    token = decrypt(requestData['token'])

    if not token:
        logInfo('not able to decrypt token')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    tokenValueList = token.split(";")

    if not isinstance(tokenValueList, list) or len(tokenValueList) != 3:
        logInfo('not valid amount of params in token provided')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    user = User.query.filter_by(id=tokenValueList[0]).first()

    if user is None or (user.status != USER_STATUS['confirmed']) or (user.email != tokenValueList[1]) or \
            user.passwordResetRequestedAt is None:
        logInfo('user not valid or mismatch with the token values')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    if user.passwordResetRequestedAt.timestamp() != float(tokenValueList[2]):
        logInfo('token expired; user_id={}'.format(user.id))
        return jsonify({'error': 'token_not_valid'}), 400

    return jsonify({'message': 'ok'})


@bp.route('/users/profile', methods=['PATCH'])
@loginRequired(USER_ROLE['user'])
def editUser():

    requestData = request.json
    validation_result = UsersSchemas.editUser(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify({'error': 'wrong_data_supplied'})

    user = User.query.get(getUserIdFromSession())

    if user is None:
        logError('user not found')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    for key, value in requestData.items():
        setattr(user, key, value)

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'ok'})


@bp.route('/users', methods=['GET'])
@loginRequired(USER_ROLE['admin'])
def getUsers():

    page = request.args.get('page', default=1, type=int)

    if page < 1:
        page = 1

    usersQuery = dbSession.query(User.id, User.email, User.name, User.surname, User.phone, User.sticksCount)

    data = {
        'users': [],
        'total': usersQuery.count(),
    }

    users = usersQuery.paginate(page, ITEMS_PER_PAGE, False)

    for user in users.items:

        userData = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'surname': user.surname,
            'phone': user.phone,
            'sticksCount': user.sticksCount
        }

        data['users'].append(userData)

    data['pages'] = users.pages

    return jsonify(data)


@bp.route('/users/<userId>/cheques', methods=['GET'])
@loginRequired(USER_ROLE['admin'])
def getUserCheques(userId):

    user = User.query.get(userId)

    if user is None:
        logError('user not found')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    cheques = Cheque.query.filter_by(userId=user.id).all()

    data = {
        'cheques': []
    }

    for cheque in cheques:
        data['cheques'].append({
            'number': cheque.number,
            'link': cheque.link if cheque.link is not None else ''
        })

    return jsonify(data)


# @bp.route('/users/reserve/prizes', methods=['POST'])
# def reservePrizes():
#     chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789@!#$%^&*()_+=-/?.><,`~"
#     phoneChars = "0123456789"
#
#     smallPrizes = [2 ,1 ,2 ,3 ,4 ,1 ,2 ,1 ,1 ,2 ,8 ,0 ,4 ,3 ,2 ,4 ,1 ,8 ,1 ,0]
#     mediumPrizes = [0 ,3 ,5 ,0 ,3 ,2 ,2 ,1 ,3 ,4 ,3 ,0 ,4 ,0 ,4 ,8 ,2 ,6 ,0 ,0]
#     bigPrizes = [2 ,5 ,3 ,6 ,1 ,4 ,6 ,8 ,2 ,5 ,10 ,2 ,2 ,5 ,8 ,2 ,9 ,7 ,10 ,3]
#
#     index = 0
#
#     with open("./users.txt", "r") as f:
#         lines = f.readlines()
#
#         for line in lines:
#             user = User(
#                 email=('.'.join(line.split(' '))).lower()[:-1] + '@gmail.com',
#                 password=bcrypt.hashpw(''.join((random.choice(chars) for x in range(8))).encode('utf-8'), bcrypt.gensalt(rounds=12)),
#                 name=line.split(' ')[0],
#                 surname=line.split(' ')[1][:-1],
#                 phone='2' + ''.join((random.choice(phoneChars) for x in range(7))),
#                 age=random.randint(18, 60),
#                 status=USER_STATUS['confirmed']
#             )
#
#             dbSession.add(user)
#             dbSession.commit()
#
#             cheque = Cheque(
#                 userId=user.id,
#                 number=''.join((random.choice(phoneChars) for x in range(8)))
#             )
#
#             db.session.add(cheque)
#
#             prizeRequest = PrizeRequest(
#                 userId=user.id,
#             )
#
#             dbSession.add(prizeRequest)
#             dbSession.commit()
#
#             prizeRequestDetails = PrizeRequestDetails(
#                 prizeRequestId=prizeRequest.id,
#                 type=PRIZE_TYPE['small'],
#                 count=smallPrizes[index]
#             )
#
#             dbSession.add(prizeRequestDetails)
#
#             prizeRequestDetails = PrizeRequestDetails(
#                 prizeRequestId=prizeRequest.id,
#                 type=PRIZE_TYPE['medium'],
#                 count=mediumPrizes[index]
#             )
#
#             dbSession.add(prizeRequestDetails)
#
#             prizeRequestDetails = PrizeRequestDetails(
#                 prizeRequestId=prizeRequest.id,
#                 type=PRIZE_TYPE['big'],
#                 count=bigPrizes[index]
#             )
#
#             dbSession.add(prizeRequestDetails)
#
#             selectedPrize = Prize.query.filter_by(type=PRIZE_TYPE['small']).first()
#
#             if selectedPrize is not None:
#                 selectedPrize.count = selectedPrize.count - smallPrizes[index]
#                 dbSession.add(selectedPrize)
#
#             selectedPrize = Prize.query.filter_by(type=PRIZE_TYPE['medium']).first()
#
#             if selectedPrize is not None:
#                 selectedPrize.count = selectedPrize.count - mediumPrizes[index]
#                 dbSession.add(selectedPrize)
#
#             selectedPrize = Prize.query.filter_by(type=PRIZE_TYPE['big']).first()
#
#             if selectedPrize is not None:
#                 selectedPrize.count = selectedPrize.count - bigPrizes[index]
#                 dbSession.add(selectedPrize)
#
#             index += 1
#
#         dbSession.commit()
#
#     return jsonify({})

