import os
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
CLIENT_KWARGS = {
    'scope': 'profile',
    'policy_hashes': ['a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447', 
                      'a8009a7a528d87778c356da3a55d964719e818666a04e4f960c9e2439e35f138',
                      'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef']
}
