import os

OAUTH2_TOKEN_EXPIRES_IN = {
    'authorization_code': 888888,
    'implicit': 3600,
    'password': 864000,
    'client_credentials': 864000
}

OAUTH2_REFRESH_TOKEN_GENERATOR = True

INTEGRITY_CHECK = os.environ.get('INTEGRITY_CHECK', 'hmac')
ENABLE_STATEFUL_AUTH = os.environ.get('ENABLE_STATEFUL_AUTH', 'True').lower() == 'true'
ENABLE_LOGGING = os.environ.get('ENABLE_LOGGING', 'True').lower() == 'true'
MACAROON = os.environ.get('MACAROON', 'False').lower() == 'true'