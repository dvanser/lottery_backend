import tempfile
from flask import Blueprint, jsonify, request
from lottery.validation_schemas.codes_schemas import CodesSchemas
from .auth import loginRequired
from .db import User, Code, Cheque, db
from .config import USER_ROLE, ALLOWED_IMAGE_FORMATS, CODE_STATUS, G_DRIVE_BASE_PATH
from .common import logInfo, logError
from .auth import getUserIdFromSession
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pathlib
from time import time

bp = Blueprint('codes', __name__)

def uploadImageToGDrive(requestFile, filename):
    try:
        with tempfile.NamedTemporaryFile() as tempImage:
            tempImage.write(requestFile.read())
            tempImage.flush()

            gauth = GoogleAuth()

            # uncomment for first authentication to save credentials and avoid authentication each time when app restarted
            # gauth.LocalWebserverAuth()
            # gauth.SaveCredentialsFile("gdrive_credentials.txt")

            # comment this line for the first authentication
            gauth.LoadCredentialsFile("gdrive_credentials.txt")

            drive = GoogleDrive(gauth)

            logInfo('starting file uploading; file_name = {}'.format(tempImage.name))

            chequeImage = drive.CreateFile({'title': filename})
            chequeImage.SetContentFile(tempImage.name)
            chequeImage.Upload()

            logInfo('file uploading finished; file_id = {}'.format(chequeImage['id']))

            tempImage.close()

            return chequeImage['id']
    except:
        return "error"


@bp.route('/codes', methods=['POST'])
@loginRequired(USER_ROLE['user'])
def addCodes():

    return jsonify({'error': 'not_found'}), 404

    requestData = request.json

    validation_result = CodesSchemas.validateAddCodes(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    if len(requestData['codes']) == 0:
        logInfo('empty codes array')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    user = User.query.get(getUserIdFromSession())

    if user is None:
        logError('user not found')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    for code in requestData['codes']:
        if Code.query.filter_by(code=code.upper(), status=CODE_STATUS['not_used']).first() is None:
            logInfo('not valid code; code={}'.format(code))
            return jsonify({'error': 'not_valid_code', 'code': code}), 400

    for code in requestData['codes']:
        code = Code.query.filter_by(code=code.upper(), status=CODE_STATUS['not_used']).first()
        code.status = CODE_STATUS['used']
        code.userId = user.id

        user.sticksCount = user.sticksCount + 1

        db.session.add(code)
        db.session.commit()

        db.session.add(user)
        db.session.commit()

    return jsonify({'message': 'ok'})


@bp.route('/cheque', methods=['POST'])
@loginRequired(USER_ROLE['user'])
def addCheque():
    user = User.query.get(getUserIdFromSession())

    if user is None:
        logError('user not found')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    if len(request.form) < 1:
        logError('number param are not provided')
        return jsonify({'error': 'number_not_provided'}), 400

    number = request.form['number']

    if number is None or number == '':
        logError('number is not provided')
        return jsonify({'error': 'number_not_provided'}), 400

    fileId = ''

    if len(request.files) != 0:

        image = request.files['cheque']
        fileExtension = pathlib.Path(image.filename).suffix

        if fileExtension.upper() not in ALLOWED_IMAGE_FORMATS:
            logError('not allowed file extension; fileExtension = {}'.format(fileExtension))
            return jsonify({'error': 'not_allowed_file_extension'}), 400

        filename = image.filename.replace(image.filename, str(int(time())) + 'uid' + str(user.id) + fileExtension)

        result = uploadImageToGDrive(image, filename)

        if result == "error":
            logError('an error occurred during file upload')
            return jsonify({'error': 'file_uploading_error'}), 400

        fileId = result

    cheque = Cheque(
        userId=user.id,
        number=number
    )

    if fileId != '':
        cheque.link = G_DRIVE_BASE_PATH + fileId

    db.session.add(cheque)
    db.session.commit()

    return jsonify({'message': 'ok'})


# in case we will be using one request form solution
# @bp.route('/cheque', methods=['POST'])
# @loginRequired(USER_ROLE['user'])
# def uploadCheque():
#
#     user = User.query.get(getUserIdFromSession())
#
#     if user is None:
#         logError('user not found')
#         return jsonify({'error': 'wrong_data_supplied'}), 400
#
#     if len(request.form) < 1:
#         logError('codes param are not provided')
#         return jsonify({'error': 'codes_not_provided'}), 400
#
#     codes = [x.strip() for x in request.form['codes'].split(',')]
#
#     if codes[0] == '':
#         logError('codes are not provided')
#         return jsonify({'error': 'codes_not_provided'}), 400
#
#     for code in codes:
#         if Code.query.filter_by(code=code, status=CODE_STATUS['not_used']).first() is None:
#                 return jsonify({'error': 'not_valid_code'}), 400
#
#     chequeNumbers = [x.strip() for x in request.form['chequeNumbers'].split(',')]
#
#     if chequeNumbers[0] == '' and len(request.files) == 0:
#         logError('cheque codes are not provided')
#         return jsonify({'error': 'cheque_codes_not_provided'}), 400
#
#     fileIds = []
#
#     if len(request.files) > 0:
#
#         for file in request.files:
#             image = request.files[file]
#             fileExtension = pathlib.Path(image.filename).suffix
#
#             if fileExtension.upper() not in ALLOWED_IMAGE_FORMATS:
#                 print(fileExtension.capitalize())
#                 logError('not allowed file extension; fileExtension = {}'.format(fileExtension))
#                 return jsonify({'error': 'not_allowed_file_extension'}), 400
#
#             filename = image.filename.replace(image.filename, str(int(time())) + 'uid' + '14' + fileExtension)
#             result = uploadImageToGDrive(image)
#
#             if result == "error":
#                 logError('an error occurred during file upload')
#                 return jsonify({'error': 'file_uploading_error'}), 400
#
#             fileIds.append(result)
#
#     if len(fileIds) > 0:
#         for i in range(len(request.files)):
#             cheque = Cheque(
#                 userId=user.id,
#                 number=request.files[i],
#                 link=G_DRIVE_BASE_PATH + fileIds[i]
#             )
#
#             db.session.add(cheque)
#             db.session.commit()
#
#     for chequeNumber in chequeNumbers:
#         cheque = Cheque(
#             userId=user.id,
#             number=chequeNumber
#         )
#
#         db.session.add(cheque)
#         db.session.commit()
#
#     for usedCode in codes:
#         code = Code.query.filter_by(code=usedCode, status=CODE_STATUS['not_used']).first()
#         code.status = CODE_STATUS['used']
#
#         db.session.add(code)
#         db.session.commit()
#
#     return jsonify({'message': 'ok'})
