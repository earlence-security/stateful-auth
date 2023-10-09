import time
import uuid
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
import uuid 

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)

    def __str__(self):
        return self.username

    def get_user_id(self):
        return self.id

    def check_password(self, password):
        return password == 'valid'


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')
    


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')

    def is_refresh_token_active(self):
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()


######################
#
# Resources
# 
######################
class Event(db.Model):
    """A simple event model for users to record events happen in the past or future."""
    __tablename__ = 'event'

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    # Mark which user this event belongs to
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')
    # Event information
    name = db.Column(db.String(40), default='(No title)')
    description = db.Column(db.String(40), default='')
    time = db.Column(db.Float, default=time.time())
    location = db.Column(db.String(40), default='')

    @property
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Email(db.Model):
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    # Mark which user this event belongs to
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    title = db.Column(db.String(40))
    content = db.Column(db.String(200))
    # Add history in resource itself for now
    history = db.Column(db.String(200))

    @property
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# TODO
# Add (obj_id/uri, history) storage, since validating history should be generic
