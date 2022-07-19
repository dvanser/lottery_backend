import logging
import traceback
import multiprocessing
from flask import Flask, request, jsonify
from datetime import timedelta, datetime
import bcrypt
from flask_jwt_extended import create_access_token, get_raw_jwt
from werkzeug.exceptions import HTTPException
from lottery import prizes
from .common import logInfo, logCritical, logError, sqlDebug, encrypt, decrypt, logDebug, sendEmail, getDictKeyByValue
from .config import USER_ROLE, USER_STATUS, CRYPTO_TOKEN_EXPIRATION, EMAIL_CONFIRMATION_URL, JWT_EXPIRATION_TIME, LANGUAGES
from .db import db, dbSession, User, Prize
from .auth import jwt, loginRequired, RevokedTokenAdmin, getAdminIdFromSession
from .validation_schemas.auth_schemas import AuthSchemas
from . import users, admins, prizes, codes
from flask_babel import Babel, gettext


class ConfigClass(object):
    ENVIRONMENT = 'prod'  # set whatever else for prod
    # BASE_URL = 'http://localhost:3000'
    BASE_URL = 'https://lottery.lv'

    # Flask settings
    JWT_SECRET_KEY = ''
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access']  # access token will be checked in blacklist, add refresh for refresh token if required

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'  # file-based SQL database for dev only
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # avoids SQLAlchemy warning

    # Flask-User settings
    USER_ENABLE_EMAIL = True  # enable email authentication
    USER_ENABLE_USERNAME = False  # enable username authentication
    DEBUG = True  # MEMO: change to False for production

    # mail config
    MAIL_SERVER = ''
    MAIL_PORT = 587
    MAIL_USE_SSL = True
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MAIL_ASCII_ATTACHMENTS = True
    # MAIL_SERVER = 'smtp.gmail.com'
    # MAIL_PORT = 465
    # MAIL_USE_SSL = True
    # MAIL_USERNAME = ''
    # MAIL_PASSWORD = ''
    # MAIL_ASCII_ATTACHMENTS = True


app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')

babel = Babel(app)
#max allowed size 10mb
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

if app.config['ENVIRONMENT'] != 'test':
    gunicornLogger = logging.getLogger('gunicorn.error')
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
    app.logger.handlers = gunicornLogger.handlers
    app.logger.setLevel(gunicornLogger.level)
else:  # MEMO: used only for dev
    from flask_cors import CORS

    CORS(app)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
    app.logger.setLevel(logging.DEBUG)

    # MEMO: dev use only! turn on SQL queries debug mode, all queries and execution time will be logged
    # app.config['SQLALCHEMY_RECORD_QUERIES'] = True
    # app.after_request(sqlDebug)

db.init_app(app)

app.register_blueprint(users.bp)
app.register_blueprint(admins.bp)
app.register_blueprint(codes.bp)
app.register_blueprint(prizes.bp)

jwt.init_app(app)

@app.route('/signup', methods=['POST'])
def signup():

    requestData = request.json

    validation_result = AuthSchemas.validateSignup(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    if requestData['password'] != requestData['repeatPassword']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    if User.query.filter_by(email=requestData['email'].lower()).first() is not None:
        logInfo('email already in use')
        return jsonify({'error': 'email_in_use'}), 400

    currentDateTime = datetime.utcnow()

    user = User(
        email=requestData['email'].lower(),
        password=bcrypt.hashpw(requestData['password'].encode('utf-8'), bcrypt.gensalt(rounds=12)),
        name=requestData['name'],
        surname=requestData['surname'],
        phone=requestData['phone'],
        age=requestData['age']
    )

    dbSession.add(user)
    dbSession.commit()

    tokenGenerationTime = currentDateTime.timestamp()

    token = str(user.id) + ';' + user.email + ';' + str(tokenGenerationTime + CRYPTO_TOKEN_EXPIRATION)

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
        '" style="height:36px;v-text-anchor:middle;width:150px;" arcsize="5%" strokecolor="#199DDF" fillcolor="#199DDF"> <w:anchorlock/> '
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

    return jsonify({})


@app.route('/login', methods=['POST'])
def login():

    requestData = request.json

    validation_result = AuthSchemas.validateLogin(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    user = User.query.filter_by(email=requestData['email'].lower()).first()

    if user is None:
        logInfo('user with provided email not found; email={}'.format(requestData['email']))
        return jsonify({'error': 'wrong_data_supplied'}), 400

    if user.status == USER_STATUS['created']:
        logInfo('user account is not confirmed; user_id={}'.format(user.id))
        return jsonify({'error': 'user_not_confirmed'}), 400

    if not bcrypt.checkpw(requestData['password'].encode('utf8'), user.password):
        logInfo('wrong credentials provided; user_id={}'.format(user.id))
        return jsonify({'error': 'wrong_data_supplied'}), 400

    accessToken = create_access_token(identity=user, expires_delta=timedelta(days=JWT_EXPIRATION_TIME))

    return jsonify(accessToken=accessToken, email=user.email, role=getDictKeyByValue(USER_ROLE, user.role))


@app.route('/logout', methods=['POST'])
@loginRequired(USER_ROLE['user'])
def logout():

    jti = get_raw_jwt()['jti']

    try:
        revoked_token = RevokedTokenAdmin(jti=jti)
        revoked_token.add()
        return jsonify({})
    except:
        return jsonify({'error': 'server_error'}), 500


def handleApplicationErrors(e):
    # generate unique error ID
    errorId = None
    adminId = getAdminIdFromSession()

    if adminId is not None:
        errorId = str(adminId) + '_' + str(datetime.utcnow().timestamp())

    logCritical('error occurred; error_id={}, error={}, traceback:\n{}'.format(errorId, e, traceback.format_exc()))

    responseData = {'error': 'server_error'}

    if errorId is not None:
        responseData['errorId'] = errorId

    return jsonify(responseData), 500


@app.errorhandler(Exception)
def handleException(e):
    # return http exceptions as is except 500 and 502 status code
    if isinstance(e, HTTPException) and e.code != 500 and e.code != 502:
        logError('error occurred; error={}'.format(e))
        return e

    return handleApplicationErrors(e)


@babel.localeselector
def getLocale():
    lang = request.accept_languages.best_match(LANGUAGES)

    if lang:
        return lang

    return 'lv'

