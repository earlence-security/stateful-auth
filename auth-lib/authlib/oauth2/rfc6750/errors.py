"""
    authlib.rfc6750.errors
    ~~~~~~~~~~~~~~~~~~~~~~

    OAuth Extensions Error Registration. When a request fails,
    the resource server responds using the appropriate HTTP
    status code and includes one of the following error codes
    in the response.

    https://tools.ietf.org/html/rfc6750#section-6.2

    :copyright: (c) 2017 by Hsiaoming Yang.
"""
from ..base import OAuth2Error

__all__ = [
    'InvalidTokenError', 'InsufficientScopeError', 'UnregisteredPolicyError', 'PolicyFailedError', 'BadPolicyEndpointError',
    'PolicyHashMismatchError', 'PolicyCrashedError', 'InvalidHistoryError'
]


class InvalidTokenError(OAuth2Error):
    """The access token provided is expired, revoked, malformed, or
    invalid for other reasons. The resource SHOULD respond with
    the HTTP 401 (Unauthorized) status code.  The client MAY
    request a new access token and retry the protected resource
    request.

    https://tools.ietf.org/html/rfc6750#section-3.1
    """
    error = 'invalid_token'
    description = (
        'The access token provided is expired, revoked, malformed, '
        'or invalid for other reasons.'
    )
    status_code = 401

    def __init__(self, description=None, uri=None, status_code=None,
                 state=None, realm=None, **extra_attributes):
        super(InvalidTokenError, self).__init__(
            description, uri, status_code, state)
        self.realm = realm
        self.extra_attributes = extra_attributes

    def get_headers(self):
        """If the protected resource request does not include authentication
        credentials or does not contain an access token that enables access
        to the protected resource, the resource server MUST include the HTTP
        "WWW-Authenticate" response header field; it MAY include it in
        response to other conditions as well.

        https://tools.ietf.org/html/rfc6750#section-3
        """
        headers = super(InvalidTokenError, self).get_headers()

        extras = []
        if self.realm:
            extras.append(f'realm="{self.realm}"')
        if self.extra_attributes:
            extras.extend([f'{k}="{self.extra_attributes[k]}"' for k in self.extra_attributes])
        extras.append(f'error="{self.error}"')
        error_description = self.get_error_description()
        extras.append(f'error_description="{error_description}"')
        headers.append(
            ('WWW-Authenticate', 'Bearer ' + ', '.join(extras))
        )
        return headers


class InsufficientScopeError(OAuth2Error):
    """The request requires higher privileges than provided by the
    access token. The resource server SHOULD respond with the HTTP
    403 (Forbidden) status code and MAY include the "scope"
    attribute with the scope necessary to access the protected
    resource.

    https://tools.ietf.org/html/rfc6750#section-3.1
    """
    error = 'insufficient_scope'
    description = 'The request requires higher privileges than provided by the access token.'
    status_code = 403

class UnregisteredPolicyError(OAuth2Error):
    """The policy program is not registered.
    """
    error = 'unregistered_policy'
    description = 'The policy program is not registered.'
    status_code = 403

class PolicyFailedError(OAuth2Error):
    """The Policy program returned false.
    """
    error = 'policy_failed'
    description = 'The Policy program denied the request.'
    status_code = 403

class BadPolicyEndpointError(OAuth2Error):
    """Could not get the policy from the Policy endpoint
    """
    error = 'bad_policy_endpoint'
    description = 'could not get the policy from the policy endpoint.'
    status_code = 403

class PolicyHashMismatchError(OAuth2Error):
    """policy_hash != hash(policy)
    """
    error = 'policy_hash_mismatch'
    description = 'policy_hash != hash(policy)'
    status_code = 403

class PolicyCrashedError(OAuth2Error):
    """policy execution unsuccessful
    """
    error = 'policy_crashed'
    description = 'policy execution unsuccessful'
    status_code = 403

class InvalidHistoryError(OAuth2Error):
    """The history is invalid.
    """
    error = 'invalid_history'
    description = 'The history is invalid.'
    status_code = 400