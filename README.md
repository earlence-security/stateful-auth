# stateful-auth

Uninstall Authlib if you have it installed

```
pip uninstall Authlib
```

Install required libraries

```
pip install -r requirements.txt
```

To start the Auth server, go to ``Authorization_Server`` folder, run

```
# disable check https
export AUTHLIB_INSECURE_TRANSPORT=1
flask run
```

Auth server will be running on ``http://127.0.0.1:5000/``

Visit the Auth server, register our Client with the Auth Server by filling in Client metadata:

```
  client_uri: 'http://127.0.0.1:8080/'
  allowed_scope: ['profile']
  policy_program_endpoint: 'http://127.0.0.1:8080/policy'
  redirect_uris: ['http://127.0.0.1:8080/auth']
  grant_types: ['authorization_code']
  response_types: ['code']
  token_endpoint_auth_method: client_secret_basic
```

Add policy hash info too

```
policy_hashes: *SHA256 of some program*, ...
```

The Auth server will provide us ``Client_id`` and ``Client_secret``

Go to Client folder and create a ``.env`` file, put in

```
CLIENT_ID=your_id
CLIENT_SECRET=your_secret
```

In ``config.py``, add policy_hashes info

```
policy_hashes: *SHA256 of some program*, ...
```

To fire up the Client, go to ``Client`` folder, run

```
# need to specify the port
flask run --port=8080
```

Client will be running on ``http://127.0.0.1:8080/``

Visit the Client, connect and consent, select which policy to enforce

Successfully got back the user's Token!

Then, use the token to access any API provided by the server as you wish.
For example, if we want to access `/api/me`.
```
curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:5000/api/me
```

For comparing performance with Macaroons, set ``'MACAROON': True,``
in ``server/app.py`` and ``client/config.py``

