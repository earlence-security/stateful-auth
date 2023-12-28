import os
from dotenv import load_dotenv
from utils import read_policy_hashes

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
CLIENT_KWARGS = {
    'scope': 'profile',
    'policy_hashes': read_policy_hashes()
}
HISTORY_DIRECTORY = os.path.join(os.getcwd(), "history")
