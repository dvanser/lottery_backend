import base64
import multiprocessing
import shutil
import tempfile
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from flask_babel import gettext
from lottery.validation_schemas.prizes_schemas import PrizesSchemas
from .auth import loginRequired, getUserIdFromSession
from .db import User, dbSession, Prize, PrizeRequest, PrizeRequestDetails
from .config import USER_ROLE, PRIZE_TYPE, DPD_BASE_URL, DPD_PARCEL_SHOP_SEARCH_URL, DPD_USERNAME, DPD_PASSWORD, \
    DPD_COUNTRY, PDP_FETCH_GS_PUDO_POINT, DPD_CREATE_SHIPMENT_URL, DPD_PARCEL_TYPE, DPD_NUM_OF_PARCEL, \
    DPD_PARCEL_PRINT_URL, PRIZE_REQUEST_STATUS, SHIPPING_TYPES
from .common import logInfo, logError, getDictKeyByValue, sendEmail, getFileContent, getLang
import requests
import json
from PIL import Image, ImageFont, ImageDraw


bp = Blueprint('prizes', __name__)

@bp.route('/prizes', methods=['GET'])
def getPrizes():

    prizes = dbSession.query(Prize.type, Prize.count, Prize.sticksNeeded).all()

    if getLang() == 'ru':
        image = Image.open("./lottery/images/counter_ru.png")
    else:
        image = Image.open("./lottery/images/counter_lv.png")

    title_font = ImageFont.truetype('./lottery/fonts/arial.ttf', 30)
    image_editable = ImageDraw.Draw(image)

    for prize in prizes:
        if prize.type == PRIZE_TYPE['small']:
            # data['small'] = {'prizesCount': prize.count, 'sticksNeeded': prize.sticksNeeded}
            image_editable.text((500, 440), str(prize.count), (0, 0, 0), font=title_font)
        elif prize.type == PRIZE_TYPE['medium']:
            # data['medium'] = {'prizesCount': prize.count, 'sticksNeeded': prize.sticksNeeded}
            image_editable.text((1000, 440), str(prize.count), (0, 0, 0), font=title_font)
        elif prize.type == PRIZE_TYPE['big']:
            # data['big'] = {'prizesCount': prize.count, 'sticksNeeded': prize.sticksNeeded}
            image_editable.text((1000, 910), str(prize.count), (0, 0, 0), font=title_font)

    image.save("result.png")

    with open("result.png", "rb") as image_file:
        return jsonify({'image': 'data:image/png;base64,' + base64.b64encode(image_file.read()).decode()})


@bp.route('/prizesCount', methods=['GET'])
@loginRequired(USER_ROLE['user'])
def getPrizesCount():

    prizes = dbSession.query(Prize.type, Prize.count, Prize.sticksNeeded).all()

    data = {}

    for prize in prizes:
        if prize.type == PRIZE_TYPE['small']:
            data['small'] = {'prizesCount': prize.count, 'sticksNeeded': prize.sticksNeeded}
        elif prize.type == PRIZE_TYPE['medium']:
            data['medium'] = {'prizesCount': prize.count, 'sticksNeeded': prize.sticksNeeded}
        elif prize.type == PRIZE_TYPE['big']:
            data['big'] = {'prizesCount': prize.count, 'sticksNeeded': prize.sticksNeeded}

    return jsonify(data)


@bp.route('/prizes/parcelshops', methods=['GET'])
@loginRequired(USER_ROLE['user'])
def getPrizesParcelshops():

    user = User.query.get(getUserIdFromSession())

    if user is None:
        logInfo('user not found the from session')
        return jsonify({'error': 'user_not_found'}), 404

    response = requests.post(
        DPD_BASE_URL + DPD_PARCEL_SHOP_SEARCH_URL + 'username=' + DPD_USERNAME + '&password='
        + DPD_PASSWORD + '&country=' + DPD_COUNTRY + '&fetchGsPUDOpoint=' + PDP_FETCH_GS_PUDO_POINT,
        headers={
            'accept': 'application/json;charset=UTF-8',
            'Content-Type': 'application/json'
        }
    )

    if response.status_code != 200:
        try:
            responseData = json.loads(response.text)
            logError('request to DPD failed; code={}, response={}'
                     .format(response.status_code, responseData))
        except:
            logError('request to DPD failed; code={} status_code={}'
                     .format(response.status_code, response))
            pass
        return {'error': 'server_error'}

    responseData = json.loads(response.text)

    if 'parcelshops' not in responseData:
        logError('parcelshops not in response')
        return {'error': 'server_error'}

    return jsonify(responseData['parcelshops'])


@bp.route('/prizes/request', methods=['POST'])
@loginRequired(USER_ROLE['user'])
def requestPrizes():

    return jsonify({'error': 'not_found'}), 404

    user = User.query.get(getUserIdFromSession())

    if user is None:
        logInfo('user not found the from session')
        return jsonify({'error': 'user_not_found'}), 404

    requestData = request.json

    if requestData['shippingType'] is None or requestData['shippingType'] not in SHIPPING_TYPES:
        logInfo('shipping type not provided or wrong value passed')
        return jsonify({'error': 'wrong_data_supplied'}), 400

    validation_result = None

    if requestData['shippingType'] == SHIPPING_TYPES[0]:
        validation_result = PrizesSchemas.validatePrizesRequestDPD(requestData)
    else:
        validation_result = PrizesSchemas.validatePrizesRequestPickUp(requestData)

    if not validation_result['success']:
        logInfo('validation failed')
        return jsonify(validation_result['error']), 400

    totalSticksNeeded = 0
    weight = 0

    for prize in requestData['prizes']:
        if prize['type'] not in PRIZE_TYPE:
            logInfo('wrong prize type; type={}'.format(prize['type']))
            return jsonify({'error': 'wrong_data_supplied'}), 400

        if not isinstance(prize['count'], int) or prize['count'] < 1:
            logInfo('wrong prize count type or amount')
            return jsonify({'error': 'wrong_data_supplied'}), 400

        selectedPrize = Prize.query.filter_by(type=PRIZE_TYPE[prize['type']]).first()

        if selectedPrize.count < prize['count']:
            logInfo('prizes are out of stock; prizesCount={}; requestedCount={}'.format(selectedPrize.count, prize['count']))
            return jsonify({'error': 'prizes_are_out_of_stocks'}), 400

        totalSticksNeeded = totalSticksNeeded + (selectedPrize.sticksNeeded * prize['count'])
        weight = round(weight + (selectedPrize.weight * prize['count']), 2)

    if user.sticksCount < totalSticksNeeded:
        logInfo('not enough sticks for selected prizes; '
                'totalSticksNeeded={}; userSticks={}'.format(totalSticksNeeded, user.sticksCount))
        return jsonify({'error': 'not_enough_sticks'}), 400

    prizeRequest = None

    if requestData['shippingType'] == SHIPPING_TYPES[0]:
        requestURL = DPD_BASE_URL + DPD_CREATE_SHIPMENT_URL + 'username=' + DPD_USERNAME + '&password=' + DPD_PASSWORD \
                     + '&name1=' + requestData['name'] + ' ' + requestData['surname'] + '&street=' + requestData['street'] \
                     + '&city=' + requestData['city'] + '&country=' + DPD_COUNTRY + '&pcode=' + requestData['pcode'] \
                     + '&phone=' + requestData['phone'] + '&parcel_type=' + DPD_PARCEL_TYPE + '&num_of_parcel=' \
                     + DPD_NUM_OF_PARCEL + '&parcelshop_id=' + requestData['parcelshopId'] + '&fetchGsPUDOpoint=' \
                     + PDP_FETCH_GS_PUDO_POINT + '&weight=' + str(weight)

        response = requests.post(
            requestURL,
            headers={
                'accept': 'application/json;charset=UTF-8',
                'Content-Type': 'application/json'
            }
        )

        if response.status_code != 200:
            try:
                responseData = json.loads(response.text)
                logError('request to DPD failed; code={}, response={}'
                         .format(response.status_code, responseData))
            except:
                logError('request to DPD failed; code={} status_code={}'
                         .format(response.status_code, response))
                pass
            return {'error': 'server_error'}

        responseData = json.loads(response.text)

        if 'pl_number' not in responseData:
            logError('parcelshops not in response')
            return {'error': 'server_error'}

        plNumbers = ''

        for plNumber in responseData['pl_number']:
            if plNumbers == '':
                plNumbers = plNumber
            else:
                plNumbers = plNumbers + '|' + plNumber

        prizeRequest = PrizeRequest(
            userId=user.id,
            plNumbers=plNumbers
        )
    else:
        prizeRequest = PrizeRequest(
            userId=user.id
        )

    dbSession.add(prizeRequest)
    dbSession.commit()

    for prize in requestData['prizes']:
        prizeRequestDetails = PrizeRequestDetails(
            prizeRequestId=prizeRequest.id,
            type=PRIZE_TYPE[prize['type']],
            count=prize['count']
        )

        dbSession.add(prizeRequestDetails)
        dbSession.commit()

    for prize in requestData['prizes']:
        selectedPrize = Prize.query.filter_by(type=PRIZE_TYPE[prize['type']]).first()

        if selectedPrize is not None:
            selectedPrize.count = selectedPrize.count - prize['count']
            dbSession.add(selectedPrize)
            dbSession.commit()

    user.sticksCount -= totalSticksNeeded

    dbSession.add(user)
    dbSession.commit()

    template = getFileContent('./lottery/templates/' + getLang() + '/confirm_order.html').decode('utf8')

    data = {
        'NAME': user.name + ' ' + user.surname,
        'ORDER_ID': prizeRequest.id,
        'DATE': datetime.utcnow().day,
        'DPD': 'Dēļu iela 4, Rīga, Latvija',
        'STICKS': user.sticksCount,
        'PHONE': user.phone,
        'EMAIL': user.email
    }

    if requestData['shippingType'] == SHIPPING_TYPES[0]:
        data['DPD'] = 'Paku Bode DPD Latvija, ' + requestData['city'] + ', ' + requestData['street']

    prizes = ''

    for prize in requestData['prizes']:
        if prize['type'] == 'small':
            if getLang() == 'ru':
                prizes += '<tr><td>' + 'Брелок:' + '</td><td>' + str(prize['count']) + '</td></tr>'
            else:
                prizes += '<tr><td>' + 'Atslēgas piekariņš:' + '</td><td>' + str(prize['count']) + '</td></tr>'

        if prize['type'] == 'medium':
            if getLang() == 'ru':
                prizes += '<tr><td>' + 'Сумка:' + '</td><td>' + str(prize['count']) + '</td></tr>'
            else:
                prizes += '<tr><td>' + 'Soma:' + '</td><td>' + str(prize['count']) + '</td></tr>'

        if prize['type'] == 'big':
            if getLang() == 'ru':
                prizes += '<tr><td>' + 'Подушка:' + '</td><td>' + str(prize['count']) + '</td></tr>'
            else:
                prizes += '<tr><td>' + 'Spilvens:' + '</td><td>' + str(prize['count']) + '</td></tr>'

    data['PRODUCTS'] = prizes

    info = ''
    delivery = ''
    dpd = ''

    if requestData['shippingType'] == SHIPPING_TYPES[0]:
        if getLang() == 'lv':
            info = 'Esam saņēmuši tavu pieprasījumu un sāksim gatavot balvu sūtīšanai uz tavu izvēlēto Pickup punktu.'
            delivery = 'Izvēlētais Pickup punkts:'
        else:
            info = 'Мы получили твою заявку и начали подготовку к отправлению в выбранный тобой пункт выдачи.'
            delivery = 'Выбранный пункт выдачи:'
        dpd = 'Paku Bode DPD Latvija, ' + requestData['city'] + ', ' + requestData['street']
    else:
        if getLang() == 'lv':
            info = 'Esam saņēmuši tavu pieprasījumu un sāksim gatavot balvu saņemšanai. Kad tā būs gatava, saņemsi ziņu no mūsu operatora.'
            delivery = 'Izvēlētais saņemšanas punkts:'
            dpd = 'Dēļu iela 4, Rīga, Latvija'
        else:
            info = 'Мы получили твою заявку и начали подготовку твоего приза. Когда он будет готов, наш оператор свяжется с тобой.'
            delivery = 'Выбранный пункт выдачи:'
            dpd = 'ул. Делю, 4-Т, Рига, Латвия'

    data['INFO'] = info
    data['DELIVERY'] = delivery

    for key, value in data.items():
        template = template.replace('??' + key + '??', str(value))

    thread = multiprocessing.Process(target=sendEmail, args=(
        user.email,
        gettext('request_prize_email_subject'),
        template
    ))

    thread.start()

    return jsonify({'message': 'ok'})


@bp.route('/prizes/requests', methods=['GET'])
@loginRequired(USER_ROLE['admin'])
def getPrizesRequests():

    prizeRequests = PrizeRequest.query.all()

    data = {
        'prizesRequests': []
    }

    if len(prizeRequests) == 0:
        return jsonify(data)

    for prizeRequest in prizeRequests:

        prizeRequestDetails = PrizeRequestDetails.query.filter_by(prizeRequestId=prizeRequest.id).all()

        prizesData = []

        for prizeRequestDetail in prizeRequestDetails:
            prizesData.append({
                'type': getDictKeyByValue(PRIZE_TYPE, prizeRequestDetail.type),
                'count': prizeRequestDetail.count
            })

        data['prizesRequests'].append({
            'id': prizeRequest.id,
            'userId': prizeRequest.userId,
            'status': getDictKeyByValue(PRIZE_REQUEST_STATUS, prizeRequest.status),
            'plNumbers': prizeRequest.plNumbers if prizeRequest.plNumbers is not None else '',
            'prizesData': prizesData
        })

    return jsonify(data)


@bp.route('/prizes/requests/<prizeRequestId>', methods=['PUT'])
@loginRequired(USER_ROLE['admin'])
def updatePrizesRequests(prizeRequestId):

    prizeRequest = PrizeRequest.query.get(prizeRequestId)

    if prizeRequest is None:
        logInfo('prizeRequests not found the from')
        return jsonify({'error': 'prize_request_not_found'}), 404

    prizeRequest.status = PRIZE_REQUEST_STATUS['sent']

    dbSession.add(prizeRequest)
    dbSession.commit()

    return jsonify({'message': 'ok'})


@bp.route('/label/<prizeRequestId>', methods=['GET'])
@loginRequired(USER_ROLE['admin'])
def getLabel(prizeRequestId):

    prizeRequest = PrizeRequest.query.get(prizeRequestId)

    if prizeRequest is None:
        logInfo('prize request id not found; prize_request_id={}'.format(prizeRequestId))
        return jsonify({'error': 'not_found'}), 404

    requestURL = DPD_BASE_URL + DPD_PARCEL_PRINT_URL + 'username=' + DPD_USERNAME + '&password=' + DPD_PASSWORD \
                 + '&parcels=' + prizeRequest.plNumbers

    response = requests.post(
        requestURL,
        stream=True,
        headers={
            'accept': 'application/json;charset=UTF-8',
            'Content-Type': 'application/json'
        }
    )

    if response.status_code != 200:
        try:
            responseData = json.loads(response.text)
            logError('request to DPD failed; code={}, response={}'
                     .format(response.status_code, responseData))
        except:
            logError('request to DPD failed; code={} status_code={}'
                     .format(response.status_code, response))
            pass
        return {'error': 'server_error'}

    with tempfile.NamedTemporaryFile() as file_object:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, file_object)

        return send_file(
            file_object.name,
            mimetype='application/pdf',
            as_attachment=True,
            attachment_filename=prizeRequest.plNumbers + '.pdf')
