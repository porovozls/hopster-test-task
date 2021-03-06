import hashlib
import hmac
import json
import time
from base64 import b64encode, b64decode, urlsafe_b64encode

from backend.settings import JWT_SECONDS_EXPIRY_TIME, JWT_SECRET


class JWTValidationError(Exception):
    def __init__(self, message, *args, **kwargs):
        super(JWTValidationError, self).__init__(*args, **kwargs)
        self.message = message


class JWTToken:

    """
    Stateful class for JWT Token
    """

    def __init__(self, token):
        self.token = token
        self.decoded_header = None
        self.decoded_payload = None
        self.parsed_header = None
        self.parsed_payload = None
        self.signature = None
        self._parse()

    def is_valid(self):
        # check expire time
        if self.parsed_payload.get("exp", 0) < int(time.time()):
            raise JWTValidationError(message="Token expired")

        # check signature
        if JWT.construct_signature(self.decoded_header, self.decoded_payload) != self.signature:
            raise JWTValidationError("Invalid token!")

    def has_permissions(self, *permissions):

        for permission in permissions:
            if permission not in self.parsed_payload["permissions"]:
                raise JWTValidationError("Permission denied for {}".format(permission))

    def _parse(self):
        try:
            header, payload, signature = self.token.split(".")
        except ValueError:
            raise JWTValidationError(message="Invalid auth token")
        try:
            self.decoded_header, self.decoded_payload = b64decode(header), b64decode(payload)
        except TypeError:
            raise JWTValidationError(message="Cannot decode token")
        try:
            self.parsed_header, self.parsed_payload = json.loads(self.decoded_header), json.loads(self.decoded_payload)
        except ValueError:
            raise JWTValidationError(message="Cannot load data from decoded token")

        self.signature = signature


class JWT:

    """
    JSON Web Token factory. Only SHA256 is supported.
    """

    def __new__(cls, *args, **kwargs):
        raise NotImplemented("Use classmethods instead of JWT instance creation")

    @classmethod
    def create_token(cls, email, *permissions):
        """
        Creates token using user email and permission scopes
        :param: email: str
        :param: scopes: list
        """
        header = cls.construct_header()
        payload = cls.construct_payload(email, *permissions)
        signature = cls.construct_signature(header, payload)
        return b64encode(header) + "." + b64encode(payload) + "." + signature

    @classmethod
    def construct_header(cls, alg="HS256"):
        """
        Return json dump of JWT header
        :param alg: str
        :return str
        """
        return json.dumps({
            "typ": "JWT",
            "alg": alg
        })

    @classmethod
    def construct_payload(cls, email, *permissions):
        """
        Return json dump of JWT payload
        :param email: str
        :param permissions: str
        :return str
        """
        return json.dumps(
            {
                "iss": "hopster",
                "exp": int(time.time()) + JWT_SECONDS_EXPIRY_TIME,
                "jti": email,
                "permissions": permissions
            }
        )

    @classmethod
    def construct_signature(cls, header, payload):
        """
        Creates signature using header and payload,
        encrypting it with SHA256 (by default)
        :param header: str
        :param payload: str
        :return: str
        """
        encoded_string = urlsafe_b64encode(header) + "." + urlsafe_b64encode(payload)
        signature = b64encode(hmac.new(JWT_SECRET, encoded_string, hashlib.sha256).hexdigest())
        return signature
