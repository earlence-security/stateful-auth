import os
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
CLIENT_KWARGS = {
    'scope': 'profile',
    'policy_hashes': ['85362e1f556df3fcc66bc05cfa9fcf09735a13a2079cf894f68be8115143003b', 
                      'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef']
}
