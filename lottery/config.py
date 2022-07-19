USER_ROLE = {
    'guest': 0,
    'user': 1,
    'admin': 2
}

USER_STATUS = {
    'created': 0,
    'confirmed': 1
}

PRIZE_TYPE = {
    'small': 0,
    'medium': 1,
    'big': 2
}

CODE_STATUS = {
    'not_used': 0,
    'used': 1
}

PRIZE_REQUEST_STATUS = {
    'active': 0,
    'sent': 1
}

LANGUAGES = [
    'ru',
    'lv'
]

SHIPPING_TYPES = [
    'DPD',
    'PICK_UP'
]

ITEMS_PER_PAGE = 50

# crypto - https://cryptography.io/en/latest/fernet/
CRYPTO_PASSWORD = b'VeryStrongPassword214'  # TODO: replace with the strong password
CRYPTO_SALT = b'2JKNNOY36W178FH8'
PASSWORD_RESET_TOKEN_EXPIRATION = 259200  # 3 days
CRYPTO_TOKEN_EXPIRATION = 259200  # 3 days

ALLOWED_IMAGE_FORMATS = ['.JPEG', '.JFIF', '.EXIF', '.TIFF', '.GIF', '.BMP', '.PNG', '.PPM',
                         '.PGM', '.PBM', '.PNM', '.WEBP', '.HDR', '.JPG', '.HEIF', '.BAT', '.SVG']

G_DRIVE_BASE_PATH = 'https://drive.google.com/file/d/'

# client env URL
# local
# CLIENT_BASE_URL = 'http://localhost:8082'
# test
CLIENT_BASE_URL = 'https://domain.lv'
# prod
# CLIENT_BASE_URL = 'https://domain.lv'

JWT_EXPIRATION_TIME = 3  # days

#links
EMAIL_CONFIRMATION_URL = '/users/email/confirm/'
RESET_PASSWORD_URL = '/reset/password/new'

#DPD configs test
DPD_BASE_URL = 'https://integration.dpd.lv/ws-mapper-rest/'
DPD_PARCEL_SHOP_SEARCH_URL = 'parcelShopSearch_?'
DPD_CREATE_SHIPMENT_URL = 'createShipment_?'
DPD_PARCEL_PRINT_URL = 'parcelPrint_?'
DPD_USERNAME = 'xxx'
DPD_PASSWORD = 'xxx'
DPD_COUNTRY = 'LV'
PDP_FETCH_GS_PUDO_POINT = '1'
DPD_PARCEL_TYPE = 'PS' #DPD pickup
DPD_NUM_OF_PARCEL = '1' #In case of shipment to Pickup point, this parameter must be “1”.

#DPD configs prod
# DPD_BASE_URL = 'https://integration.dpd.lv/ws-mapper-rest/'
# DPD_PARCEL_SHOP_SEARCH_URL = 'parcelShopSearch_?'
# DPD_CREATE_SHIPMENT_URL = 'createShipment_?'
# DPD_PARCEL_PRINT_URL = 'parcelPrint_?'
# DPD_USERNAME = 'xxx'
# DPD_PASSWORD = 'xxx'
# DPD_COUNTRY = 'LV'
# PDP_FETCH_GS_PUDO_POINT = 1
# DPD_PARCEL_TYPE = 'PS' #DPD pickup
# DPD_NUM_OF_PARCEL = '1' #In case of shipment to Pickup point, this parameter must be “1”.
