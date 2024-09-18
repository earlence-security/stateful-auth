# Installation
Uninstall Authlib if you have it installed

```
pip uninstall Authlib
```

Install required libraries

```
pip install -r requirements.txt
```

To start the Auth server, go to ``server`` folder, run


# Test on Local Machine
To start the server:
```python
cd server
# disable check https
export AUTHLIB_INSECURE_TRANSPORT=1
flask run
```

Auth server will be running on ``http://127.0.0.1:5000/``

Visit the Auth server, register our Client with the Auth Server by filling in Client metadata:

```
Client Name: client_00
Client URI: http://127.0.0.1:8080
Allowed Scope: profile
Upload Policy WASM: Upload [`client/policies/77a6a23a3c4d424dba1e7efae21cef16d01f156c6d0194e406c98cf46c22bf37.wasm`](https://github.com/earlence-security/stateful-auth/blob/eval/client/policies/77a6a23a3c4d424dba1e7efae21cef16d01f156c6d0194e406c98cf46c22bf37.wasm)
Upload State Updater WASM: Upload [`client/update_program/update_program.wasm`](https://github.com/earlence-security/stateful-auth/blob/eval/client/update_program/update_program.wasm)
Redirect URIs: http://127.0.0.1:8080
Allowed Grant Types: authorization_code
Allowed Response Types: code
Token Endpoint Auth Method: client_secret_basic
```

The Auth server will provide us `client_id` and `client_secret`


To fire up the Client, go to ``client`` folder, run

```bash
cd client
flask run --port=8080    # need to specify the port
```

Client will be running on ``http://127.0.0.1:8080/``

Visit the http://127.0.0.1:8080, connect and consent, select which policy hash we uploaded in registration.

Successfully got back the user's Token!

Then, use the token to access any API provided by the server as you wish.
For example, if we want to access `/api/me`.
```
curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:5000/api/me
```

<!-- For comparing performance with Macaroons, set ``'MACAROON': True,``
in ``server/app.py`` and ``client/config.py`` -->