from unittest import mock
from authlib.jose import JsonWebKey
from authlib.oidc.core.grants.util import generate_id_token
from authlib.integrations.django_client import OAuth, OAuthError
from authlib.common.urls import urlparse, url_decode
from django.test import override_settings
from tests.django_helper import TestCase
from ..util import (
    mock_send_value,
    get_bearer_token
)

dev_client = {
    'client_id': 'dev-key',
    'client_secret': 'dev-secret'
}


class DjangoOAuthTest(TestCase):
    def test_register_remote_app(self):
        oauth = OAuth()
        self.assertRaises(AttributeError, lambda: oauth.dev)

        oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            request_token_url='https://i.b/reqeust-token',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize'
        )
        self.assertEqual(oauth.dev.name, 'dev')
        self.assertEqual(oauth.dev.client_id, 'dev')

    def test_register_with_overwrite(self):
        oauth = OAuth()
        oauth.register(
            'dev_overwrite',
            overwrite=True,
            client_id='dev',
            client_secret='dev',
            request_token_url='https://i.b/reqeust-token',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            access_token_params={
                'foo': 'foo'
            },
            authorize_url='https://i.b/authorize'
        )
        self.assertEqual(oauth.dev_overwrite.client_id, 'dev-client-id')
        self.assertEqual(
            oauth.dev_overwrite.access_token_params['foo'], 'foo-1')

    @override_settings(AUTHLIB_OAUTH_CLIENTS={'dev': dev_client})
    def test_register_from_settings(self):
        oauth = OAuth()
        oauth.register('dev')
        self.assertEqual(oauth.dev.client_id, 'dev-key')
        self.assertEqual(oauth.dev.client_secret, 'dev-secret')

    def test_oauth1_authorize(self):
        request = self.factory.get('/login')
        request.session = self.factory.session

        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            request_token_url='https://i.b/reqeust-token',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
        )

        with mock.patch('requests.sessions.Session.send') as send:
            send.return_value = mock_send_value('oauth_token=foo&oauth_verifier=baz')

            resp = client.authorize_redirect(request)
            self.assertEqual(resp.status_code, 302)
            url = resp.get('Location')
            self.assertIn('oauth_token=foo', url)

        request2 = self.factory.get(url)
        request2.session = request.session
        with mock.patch('requests.sessions.Session.send') as send:
            send.return_value = mock_send_value('oauth_token=a&oauth_token_secret=b')
            token = client.authorize_access_token(request2)
            self.assertEqual(token['oauth_token'], 'a')

    def test_oauth2_authorize(self):
        request = self.factory.get('/login')
        request.session = self.factory.session

        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
        )
        rv = client.authorize_redirect(request, 'https://a.b/c')
        self.assertEqual(rv.status_code, 302)
        url = rv.get('Location')
        self.assertIn('state=', url)
        state = dict(url_decode(urlparse.urlparse(url).query))['state']

        with mock.patch('requests.sessions.Session.send') as send:
            send.return_value = mock_send_value(get_bearer_token())
            request2 = self.factory.get('/authorize?state={}'.format(state))
            request2.session = request.session

            token = client.authorize_access_token(request2)
            self.assertEqual(token['access_token'], 'a')

    def test_oauth2_authorize_access_denied(self):
        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
        )

        with mock.patch('requests.sessions.Session.send'):
            request = self.factory.get('/?error=access_denied&error_description=Not+Allowed')
            request.session = self.factory.session
            self.assertRaises(OAuthError, client.authorize_access_token, request)

    def test_oauth2_authorize_code_challenge(self):
        request = self.factory.get('/login')
        request.session = self.factory.session

        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
            client_kwargs={'code_challenge_method': 'S256'},
        )
        rv = client.authorize_redirect(request, 'https://a.b/c')
        self.assertEqual(rv.status_code, 302)
        url = rv.get('Location')
        self.assertIn('state=', url)
        self.assertIn('code_challenge=', url)

        state = dict(url_decode(urlparse.urlparse(url).query))['state']
        state_data = request.session[f'_state_dev_{state}']['data']
        verifier = state_data['code_verifier']

        def fake_send(sess, req, **kwargs):
            self.assertIn('code_verifier={}'.format(verifier), req.body)
            return mock_send_value(get_bearer_token())

        with mock.patch('requests.sessions.Session.send', fake_send):
            request2 = self.factory.get('/authorize?state={}'.format(state))
            request2.session = request.session
            token = client.authorize_access_token(request2)
            self.assertEqual(token['access_token'], 'a')

    def test_oauth2_authorize_code_verifier(self):
        request = self.factory.get('/login')
        request.session = self.factory.session

        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
            client_kwargs={'code_challenge_method': 'S256'},
        )
        state = 'foo'
        code_verifier = 'bar'
        rv = client.authorize_redirect(
            request, 'https://a.b/c',
            state=state, code_verifier=code_verifier
        )
        self.assertEqual(rv.status_code, 302)
        url = rv.get('Location')
        self.assertIn('state=', url)
        self.assertIn('code_challenge=', url)

        with mock.patch('requests.sessions.Session.send') as send:
            send.return_value = mock_send_value(get_bearer_token())

            request2 = self.factory.get('/authorize?state={}'.format(state))
            request2.session = request.session

            token = client.authorize_access_token(request2)
            self.assertEqual(token['access_token'], 'a')

    def test_openid_authorize(self):
        request = self.factory.get('/login')
        request.session = self.factory.session
        secret_key = JsonWebKey.import_key('secret', {'kty': 'oct', 'kid': 'f'})

        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            jwks={'keys': [secret_key.as_dict()]},
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
            client_kwargs={'scope': 'openid profile'},
        )

        resp = client.authorize_redirect(request, 'https://b.com/bar')
        self.assertEqual(resp.status_code, 302)
        url = resp.get('Location')
        self.assertIn('nonce=', url)
        query_data = dict(url_decode(urlparse.urlparse(url).query))

        token = get_bearer_token()
        token['id_token'] = generate_id_token(
            token, {'sub': '123'}, secret_key,
            alg='HS256', iss='https://i.b',
            aud='dev', exp=3600, nonce=query_data['nonce'],
        )
        state = query_data['state']
        with mock.patch('requests.sessions.Session.send') as send:
            send.return_value = mock_send_value(token)

            request2 = self.factory.get('/authorize?state={}&code=foo'.format(state))
            request2.session = request.session

            token = client.authorize_access_token(request2)
            self.assertEqual(token['access_token'], 'a')
            self.assertIn('userinfo', token)
            self.assertEqual(token['userinfo']['sub'], '123')

    def test_oauth2_access_token_with_post(self):
        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
        )
        payload = {'code': 'a', 'state': 'b'}

        with mock.patch('requests.sessions.Session.send') as send:
            send.return_value = mock_send_value(get_bearer_token())
            request = self.factory.post('/token', data=payload)
            request.session = self.factory.session
            request.session['_state_dev_b'] = {'data': {}}
            token = client.authorize_access_token(request)
            self.assertEqual(token['access_token'], 'a')

    def test_with_fetch_token_in_oauth(self):
        def fetch_token(name, request):
            return {'access_token': name, 'token_type': 'bearer'}

        oauth = OAuth(fetch_token=fetch_token)
        client = oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize'
        )

        def fake_send(sess, req, **kwargs):
            self.assertEqual(sess.token['access_token'], 'dev')
            return mock_send_value(get_bearer_token())

        with mock.patch('requests.sessions.Session.send', fake_send):
            request = self.factory.get('/login')
            client.get('/user', request=request)

    def test_with_fetch_token_in_register(self):
        def fetch_token(request):
            return {'access_token': 'dev', 'token_type': 'bearer'}

        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize',
            fetch_token=fetch_token,
        )

        def fake_send(sess, req, **kwargs):
            self.assertEqual(sess.token['access_token'], 'dev')
            return mock_send_value(get_bearer_token())

        with mock.patch('requests.sessions.Session.send', fake_send):
            request = self.factory.get('/login')
            client.get('/user', request=request)

    def test_request_without_token(self):
        oauth = OAuth()
        client = oauth.register(
            'dev',
            client_id='dev',
            client_secret='dev',
            api_base_url='https://i.b/api',
            access_token_url='https://i.b/token',
            authorize_url='https://i.b/authorize'
        )

        def fake_send(sess, req, **kwargs):
            auth = req.headers.get('Authorization')
            self.assertIsNone(auth)
            resp = mock.MagicMock()
            resp.text = 'hi'
            resp.status_code = 200
            return resp

        with mock.patch('requests.sessions.Session.send', fake_send):
            resp = client.get('/api/user', withhold_token=True)
            self.assertEqual(resp.text, 'hi')
            self.assertRaises(OAuthError, client.get, 'https://i.b/api/user')
