from flask import json, current_app
from authlib.common.urls import urlparse, url_decode, url_encode
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from authlib.oidc.core.grants import OpenIDCode as _OpenIDCode
from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant as _AuthorizationCodeGrant,
)
from tests.util import read_file_path
from .models import db, User, Client, exists_nonce
from .models import CodeGrantMixin, save_authorization_code
from .oauth2_server import TestCase
from .oauth2_server import create_authorization_server


class AuthorizationCodeGrant(CodeGrantMixin, _AuthorizationCodeGrant):
    def save_authorization_code(self, code, request):
        return save_authorization_code(code, request)


class OpenIDCode(_OpenIDCode):
    def get_jwt_config(self, grant):
        key = current_app.config['OAUTH2_JWT_KEY']
        alg = current_app.config['OAUTH2_JWT_ALG']
        iss = current_app.config['OAUTH2_JWT_ISS']
        return dict(key=key, alg=alg, iss=iss, exp=3600)

    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)

    def generate_user_info(self, user, scopes):
        return user.generate_user_info(scopes)


class BaseTestCase(TestCase):
    def config_app(self):
        self.app.config.update({
            'OAUTH2_JWT_ISS': 'Authlib',
            'OAUTH2_JWT_KEY': 'secret',
            'OAUTH2_JWT_ALG': 'HS256',
        })

    def prepare_data(self):
        self.config_app()
        server = create_authorization_server(self.app)
        server.register_grant(AuthorizationCodeGrant, [OpenIDCode()])

        user = User(username='foo')
        db.session.add(user)
        db.session.commit()

        client = Client(
            user_id=user.id,
            client_id='code-client',
            client_secret='code-secret',
        )
        client.set_client_metadata({
            'redirect_uris': ['https://a.b'],
            'scope': 'openid profile address',
            'response_types': ['code'],
            'grant_types': ['authorization_code'],
        })
        db.session.add(client)
        db.session.commit()


class OpenIDCodeTest(BaseTestCase):
    def test_authorize_token(self):
        self.prepare_data()
        rv = self.client.post('/oauth/authorize', data={
            'response_type': 'code',
            'client_id': 'code-client',
            'state': 'bar',
            'scope': 'openid profile',
            'redirect_uri': 'https://a.b',
            'user_id': '1'
        })
        self.assertIn('code=', rv.location)

        params = dict(url_decode(urlparse.urlparse(rv.location).query))
        self.assertEqual(params['state'], 'bar')

        code = params['code']
        headers = self.create_basic_header('code-client', 'code-secret')
        rv = self.client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'redirect_uri': 'https://a.b',
            'code': code,
        }, headers=headers)
        resp = json.loads(rv.data)
        self.assertIn('access_token', resp)
        self.assertIn('id_token', resp)

        claims = jwt.decode(
            resp['id_token'], 'secret',
            claims_cls=CodeIDToken,
            claims_options={'iss': {'value': 'Authlib'}}
        )
        claims.validate()

    def test_pure_code_flow(self):
        self.prepare_data()
        rv = self.client.post('/oauth/authorize', data={
            'response_type': 'code',
            'client_id': 'code-client',
            'state': 'bar',
            'scope': 'profile',
            'redirect_uri': 'https://a.b',
            'user_id': '1'
        })
        self.assertIn('code=', rv.location)

        params = dict(url_decode(urlparse.urlparse(rv.location).query))
        self.assertEqual(params['state'], 'bar')

        code = params['code']
        headers = self.create_basic_header('code-client', 'code-secret')
        rv = self.client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'redirect_uri': 'https://a.b',
            'code': code,
        }, headers=headers)
        resp = json.loads(rv.data)
        self.assertIn('access_token', resp)
        self.assertNotIn('id_token', resp)

    def test_nonce_replay(self):
        self.prepare_data()
        data = {
            'response_type': 'code',
            'client_id': 'code-client',
            'user_id': '1',
            'state': 'bar',
            'nonce': 'abc',
            'scope': 'openid profile',
            'redirect_uri': 'https://a.b'
        }
        rv = self.client.post('/oauth/authorize', data=data)
        self.assertIn('code=', rv.location)

        rv = self.client.post('/oauth/authorize', data=data)
        self.assertIn('error=', rv.location)

    def test_prompt(self):
        self.prepare_data()
        params = [
            ('response_type', 'code'),
            ('client_id', 'code-client'),
            ('state', 'bar'),
            ('nonce', 'abc'),
            ('scope', 'openid profile'),
            ('redirect_uri', 'https://a.b')
        ]
        query = url_encode(params)
        rv = self.client.get('/oauth/authorize?' + query)
        self.assertEqual(rv.data, b'login')

        query = url_encode(params + [('user_id', '1')])
        rv = self.client.get('/oauth/authorize?' + query)
        self.assertEqual(rv.data, b'ok')

        query = url_encode(params + [('prompt', 'login')])
        rv = self.client.get('/oauth/authorize?' + query)
        self.assertEqual(rv.data, b'login')


class RSAOpenIDCodeTest(BaseTestCase):
    def config_app(self):
        self.app.config.update({
            'OAUTH2_JWT_ISS': 'Authlib',
            'OAUTH2_JWT_KEY': read_file_path('jwk_private.json'),
            'OAUTH2_JWT_ALG': 'RS256',
        })

    def get_validate_key(self):
        return read_file_path('jwk_public.json')

    def test_authorize_token(self):
        # generate refresh token
        self.prepare_data()
        rv = self.client.post('/oauth/authorize', data={
            'response_type': 'code',
            'client_id': 'code-client',
            'state': 'bar',
            'scope': 'openid profile',
            'redirect_uri': 'https://a.b',
            'user_id': '1'
        })
        self.assertIn('code=', rv.location)

        params = dict(url_decode(urlparse.urlparse(rv.location).query))
        self.assertEqual(params['state'], 'bar')

        code = params['code']
        headers = self.create_basic_header('code-client', 'code-secret')
        rv = self.client.post('/oauth/token', data={
            'grant_type': 'authorization_code',
            'redirect_uri': 'https://a.b',
            'code': code,
        }, headers=headers)
        resp = json.loads(rv.data)
        self.assertIn('access_token', resp)
        self.assertIn('id_token', resp)

        claims = jwt.decode(
            resp['id_token'],
            self.get_validate_key(),
            claims_cls=CodeIDToken,
            claims_options={'iss': {'value': 'Authlib'}}
        )
        claims.validate()


class JWKSOpenIDCodeTest(RSAOpenIDCodeTest):
    def config_app(self):
        self.app.config.update({
            'OAUTH2_JWT_ISS': 'Authlib',
            'OAUTH2_JWT_KEY': read_file_path('jwks_private.json'),
            'OAUTH2_JWT_ALG': 'PS256',
        })

    def get_validate_key(self):
        return read_file_path('jwks_public.json')


class ECOpenIDCodeTest(RSAOpenIDCodeTest):
    def config_app(self):
        self.app.config.update({
            'OAUTH2_JWT_ISS': 'Authlib',
            'OAUTH2_JWT_KEY': read_file_path('secp521r1-private.json'),
            'OAUTH2_JWT_ALG': 'ES512',
        })

    def get_validate_key(self):
        return read_file_path('secp521r1-public.json')


class PEMOpenIDCodeTest(RSAOpenIDCodeTest):
    def config_app(self):
        self.app.config.update({
            'OAUTH2_JWT_ISS': 'Authlib',
            'OAUTH2_JWT_KEY': read_file_path('rsa_private.pem'),
            'OAUTH2_JWT_ALG': 'RS256',
        })

    def get_validate_key(self):
        return read_file_path('rsa_public.pem')
