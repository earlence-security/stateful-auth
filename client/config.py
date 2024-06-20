import os
from dotenv import load_dotenv
from utils import read_policy_hashes

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN_URL = os.getenv('ACCESS_TOKEN_URL')
AUTHORIZE_URL = os.getenv('AUTHORIZE_URL')
REDIRECT_URI = os.getenv('REDIRECT_URI')
CLIENT_KWARGS = {
    'scope': 'profile',
    'policy_hashes': read_policy_hashes()
}
HISTORY_DIRECTORY = os.path.join(os.getcwd(), "history")
MACAROON = os.getenv('MACAROON', False) 