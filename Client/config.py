import os
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
CLIENT_KWARGS = {
    'scope': 'profile',
    'policy_hashes': ['6e6d2741b322902cbdfb1c37d991a80136423d2dad84ca430c3b1edbe05ca6df', 
                      'e0603155c979d385b4a8c1adc8652677bfdeb486e7402969be9b72db576c5661',
                      'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef']
}
