import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app, request
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
from .auth import getSessionId
from .config import CRYPTO_SALT, CRYPTO_PASSWORD, LANGUAGES
from flask_sqlalchemy import get_debug_queries
import smtplib


def getDictKeyByValue(dictionary, value):

    if value is None:
        return value

    return list(dictionary.keys())[list(dictionary.values()).index(value)]


def encrypt(stringToEncrypt):

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=CRYPTO_SALT,
        iterations=100000,
        backend=default_backend())

    key = base64.urlsafe_b64encode(kdf.derive(CRYPTO_PASSWORD))

    f = Fernet(key)

    return f.encrypt(stringToEncrypt.encode()).decode()


def decrypt(stringToDecrypt):

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=CRYPTO_SALT,
        iterations=100000,
        backend=default_backend())

    key = base64.urlsafe_b64encode(kdf.derive(CRYPTO_PASSWORD))

    f = Fernet(key)

    try:
        return f.decrypt(stringToDecrypt.encode('utf-8')).decode()
    except:
        return False


def logMsg(msg, level='debug'):

    # get client IP
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr

    # get caller method and file names
    frame = sys._getframe(2)
    filename = frame.f_code.co_filename.split('/')[-1]
    method = frame.f_code.co_name

    # get session token if available
    sessionId = getSessionId()

    if sessionId is not None:
        msg = ip + ' [' + sessionId + '] ' + filename + ':' + method + ': ' + msg
    else:
        msg = ip + ' ' + filename + ':' + method + ': ' + msg

    if level == 'debug':
        current_app.logger.debug(msg)
    elif level == 'error':
        current_app.logger.error(msg)
    elif level == 'critical':
        current_app.logger.critical(msg)
    else:  # info
        current_app.logger.info(msg)


def logDebug(msg):
    logMsg(msg, 'debug')


def logInfo(msg):
    logMsg(msg, 'info')


def logError(msg):
    logMsg(msg, 'error')


def logCritical(msg):
    logMsg(msg, 'critical')


def sqlDebug(response):
    queries = list(get_debug_queries())
    query_str = ''
    total_duration = 0.0
    for q in queries:
        total_duration += q.duration

        stmt = str(q.statement)

        for param in q.parameters:
            stmt = stmt.replace('?', str(param), 1)

        query_str += 'Query: {}\nDuration: {}ms\n\n'.format(stmt, round(q.duration * 1000, 2))

    logDebug(('=' * 80) + ' SQL Queries - {} Queries Executed in {}ms'
             .format(len(queries), round(total_duration * 1000, 2)))
    logDebug(query_str + '\n' + ('=' * 80))

    return response


# def sendEmail(recipients, subject, html):
#
#     from . import app
#     with app.app_context():
#         msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=recipients)
#         msg.html = html
#
#         mail = Mail(current_app)
#
#         mail.send(msg)

def sendEmail(recipients, subject, html):
    from . import app

    with app.app_context():
        mailserver = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = recipients

        text = MIMEText(html, "html")
        msg.attach(text)
        mailserver.sendmail(current_app.config['MAIL_USERNAME'], recipients, msg.as_string())
        mailserver.quit()


def getFileContent(filename):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except IOError:
        logDebug('getFileContent: Could not open file')


def getLang():
    lang = request.accept_languages.best_match(LANGUAGES)

    if lang:
        return lang

    return 'lv'