import unittest
import datetime
from authlib.jose import errors
from authlib.jose import JsonWebToken, JWTClaims, jwt
from authlib.jose.errors import UnsupportedAlgorithmError
from tests.util import read_file_path


class JWTTest(unittest.TestCase):
    def test_init_algorithms(self):
        _jwt = JsonWebToken(['RS256'])
        self.assertRaises(
            UnsupportedAlgorithmError,
            _jwt.encode, {'alg': 'HS256'}, {}, 'k'
        )

        _jwt = JsonWebToken('RS256')
        self.assertRaises(
            UnsupportedAlgorithmError,
            _jwt.encode, {'alg': 'HS256'}, {}, 'k'
        )

    def test_encode_sensitive_data(self):
        # check=False won't raise error
        jwt.encode({'alg': 'HS256'}, {'password': ''}, 'k', check=False)
        self.assertRaises(
            errors.InsecureClaimError,
            jwt.encode, {'alg': 'HS256'},  {'password': ''}, 'k'
        )
        self.assertRaises(
            errors.InsecureClaimError,
            jwt.encode, {'alg': 'HS256'}, {'text': '4242424242424242'}, 'k'
        )

    def test_encode_datetime(self):
        now = datetime.datetime.utcnow()
        id_token = jwt.encode({'alg': 'HS256'}, {'exp': now}, 'k')
        claims = jwt.decode(id_token, 'k')
        self.assertIsInstance(claims.exp, int)

    def test_validate_essential_claims(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'iss': 'foo'}, 'k')
        claims_options = {
            'iss': {
                'essential': True,
                'values': ['foo']
            }
        }
        claims = jwt.decode(id_token, 'k', claims_options=claims_options)
        claims.validate()

        claims.options = {'sub': {'essential': True}}
        self.assertRaises(
            errors.MissingClaimError,
            claims.validate
        )

    def test_attribute_error(self):
        claims = JWTClaims({'iss': 'foo'}, {'alg': 'HS256'})
        self.assertRaises(AttributeError, lambda: claims.invalid)

    def test_invalid_values(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'iss': 'foo'}, 'k')
        claims_options = {'iss': {'values': ['bar']}}
        claims = jwt.decode(id_token, 'k', claims_options=claims_options)
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate,
        )
        claims.options = {'iss': {'value': 'bar'}}
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate,
        )

    def test_validate_expected_issuer_received_None(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'iss': None, 'sub': None}, 'k')
        claims_options = {
            'iss': {
                'essential': True,
                'values': ['foo']
            }
        }
        claims = jwt.decode(id_token, 'k', claims_options=claims_options)
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate
        )

    def test_validate_aud(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'aud': 'foo'}, 'k')
        claims_options = {
            'aud': {
                'essential': True,
                'value': 'foo'
            }
        }
        claims = jwt.decode(id_token, 'k', claims_options=claims_options)
        claims.validate()

        claims.options = {
            'aud': {'values': ['bar']}
        }
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate
        )

        id_token = jwt.encode({'alg': 'HS256'}, {'aud': ['foo', 'bar']}, 'k')
        claims = jwt.decode(id_token, 'k', claims_options=claims_options)
        claims.validate()
        # no validate
        claims.options = {'aud': {'values': []}}
        claims.validate()

    def test_validate_exp(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'exp': 'invalid'}, 'k')
        claims = jwt.decode(id_token, 'k')
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate
        )

        id_token = jwt.encode({'alg': 'HS256'}, {'exp': 1234}, 'k')
        claims = jwt.decode(id_token, 'k')
        self.assertRaises(
            errors.ExpiredTokenError,
            claims.validate
        )

    def test_validate_nbf(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'nbf': 'invalid'}, 'k')
        claims = jwt.decode(id_token, 'k')
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate
        )

        id_token = jwt.encode({'alg': 'HS256'}, {'nbf': 1234}, 'k')
        claims = jwt.decode(id_token, 'k')
        claims.validate()

        id_token = jwt.encode({'alg': 'HS256'}, {'nbf': 1234}, 'k')
        claims = jwt.decode(id_token, 'k')
        self.assertRaises(
            errors.InvalidTokenError,
            claims.validate, 123
        )

    def test_validate_iat_issued_in_future(self):
        in_future = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
        id_token = jwt.encode({'alg': 'HS256'}, {'iat': in_future}, 'k')
        claims = jwt.decode(id_token, 'k')
        with self.assertRaises(errors.InvalidTokenError) as error_ctx:
            claims.validate()
        self.assertEqual(
            str(error_ctx.exception),
            'invalid_token: The token is not valid as it was issued in the future'
        )

    def test_validate_iat_issued_in_future_with_insufficient_leeway(self):
        in_future = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
        id_token = jwt.encode({'alg': 'HS256'}, {'iat': in_future}, 'k')
        claims = jwt.decode(id_token, 'k')
        with self.assertRaises(errors.InvalidTokenError) as error_ctx:
            claims.validate(leeway=5)
        self.assertEqual(
            str(error_ctx.exception),
            'invalid_token: The token is not valid as it was issued in the future'
        )

    def test_validate_iat_issued_in_future_with_sufficient_leeway(self):
        in_future = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
        id_token = jwt.encode({'alg': 'HS256'}, {'iat': in_future}, 'k')
        claims = jwt.decode(id_token, 'k')
        claims.validate(leeway=20)

    def test_validate_iat_issued_in_past(self):
        in_future = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        id_token = jwt.encode({'alg': 'HS256'}, {'iat': in_future}, 'k')
        claims = jwt.decode(id_token, 'k')
        claims.validate()

    def test_validate_iat(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'iat': 'invalid'}, 'k')
        claims = jwt.decode(id_token, 'k')
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate
        )

    def test_validate_jti(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'jti': 'bar'}, 'k')
        claims_options = {
            'jti': {
                'validate': lambda c, o: o == 'foo'
            }
        }
        claims = jwt.decode(id_token, 'k', claims_options=claims_options)
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate
        )

    def test_validate_custom(self):
        id_token = jwt.encode({'alg': 'HS256'}, {'custom': 'foo'}, 'k')
        claims_options = {
            'custom': {
                'validate': lambda c, o: o == 'bar'
            }
        }
        claims = jwt.decode(id_token, 'k', claims_options=claims_options)
        self.assertRaises(
            errors.InvalidClaimError,
            claims.validate
        )

    def test_use_jws(self):
        payload = {'name': 'hi'}
        private_key = read_file_path('rsa_private.pem')
        pub_key = read_file_path('rsa_public.pem')
        data = jwt.encode({'alg': 'RS256'}, payload, private_key)
        self.assertEqual(data.count(b'.'), 2)

        claims = jwt.decode(data, pub_key)
        self.assertEqual(claims['name'], 'hi')

    def test_use_jwe(self):
        payload = {'name': 'hi'}
        private_key = read_file_path('rsa_private.pem')
        pub_key = read_file_path('rsa_public.pem')
        _jwt = JsonWebToken(['RSA-OAEP', 'A256GCM'])
        data = _jwt.encode(
            {'alg': 'RSA-OAEP', 'enc': 'A256GCM'},
            payload, pub_key
        )
        self.assertEqual(data.count(b'.'), 4)

        claims = _jwt.decode(data, private_key)
        self.assertEqual(claims['name'], 'hi')

    def test_use_jwks(self):
        header = {'alg': 'RS256', 'kid': 'abc'}
        payload = {'name': 'hi'}
        private_key = read_file_path('jwks_private.json')
        pub_key = read_file_path('jwks_public.json')
        data = jwt.encode(header, payload, private_key)
        self.assertEqual(data.count(b'.'), 2)
        claims = jwt.decode(data, pub_key)
        self.assertEqual(claims['name'], 'hi')

    def test_with_ec(self):
        payload = {'name': 'hi'}
        private_key = read_file_path('secp521r1-private.json')
        pub_key = read_file_path('secp521r1-public.json')
        data = jwt.encode({'alg': 'ES512'}, payload, private_key)
        self.assertEqual(data.count(b'.'), 2)

        claims = jwt.decode(data, pub_key)
        self.assertEqual(claims['name'], 'hi')
