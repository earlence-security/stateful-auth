import flask
from flask import Blueprint, jsonify
from authlib.integrations.flask_oauth2 import current_token
import json

from .oauth2 import require_oauth
from .oauth2 import require_oauth_stateful
from .models import db, Event, Email

resource_bp = Blueprint("resource", __name__)

# TODO: ResourceProtector.acquire_token. 
# See https://github.com/lepture/authlib/blob/master/authlib/integrations/flask_oauth2/resource_protector.py
@resource_bp.route('/me')
@require_oauth_stateful()
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)


# Dummy api to demonstrate stateless policies
@resource_bp.route('/me2')
@require_oauth_stateful()
def api_me2():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)


# Another Dummy api to demonstrate stateless policies
@resource_bp.route('/send-money', methods=['POST'])
@require_oauth_stateful()
def send_money():
    data = flask.request.get_json()
    if 'recipient' in data and 'amount' in data:
        recipient = data['recipient']
        amount = data['amount']
        # Transfer the money
        result = {
            'message': f'Successfully sent ${amount} to {recipient}',
            'recipient': recipient,
            'amount': amount
        }
        return jsonify(result), 200
    else:
        return jsonify({'error': 'Invalid request. Please provide recipient and amount.'}), 400


@resource_bp.route('/emails/<emailId>', methods=['GET', 'DELETE'])
@require_oauth_stateful()
def get_or_delete_emails(emailId):
    '''Endpoint for get or delete an email.'''
    user = current_token.user
    email = Email.query.filter_by(id=emailId).first()
    # If the event does not belong to the current user, abort.
    if not email:
        # Bad request
        flask.abort(400)
    if email.user_id != user.id:
        # Forbidden
        flask.abort(403)
    if flask.request.method == 'GET':
        return jsonify(email.as_dict())
    else:
        db.session.delete(email)
        db.session.commit()
        return 'deleted', 204

@resource_bp.route('/emails', methods=['GET', 'POST'])
@require_oauth_stateful()
def list_or_insert_email():
    '''Endpoint for list all the events or insert an new email.'''
    user = current_token.user
    if flask.request.method == 'GET':
        emails = Email.query.filter_by(user_id=user.id).all()
        email_json = []
        for email in emails:
            email_json.append(email.as_dict())
        return jsonify(user_id=user.id, results=email_json)
    else:
        email_request = flask.request.get_json()
        email = Email(
            user_id=user.id,
            title=email_request.get('title'),
            content=email_request.get('content'),
        )
        db.session.add(email)
        db.session.commit()
        return jsonify(email.as_dict()), 201


@resource_bp.route('/events/<int:eventId>', methods=['GET', 'DELETE'])
@require_oauth('events')
def get_or_delete_event(eventId):
    '''Endpoint for get or delete an event.'''
    user = current_token.user
    event = Event.query.filter_by(id=eventId).first()
    # If the event does not belong to the current user, abort.
    if not event:
        # Bad request
        flask.abort(400)
    if event.user_id != user.id:
        # Forbidden
        flask.abort(403)
    if flask.request.method == 'GET':
        return jsonify(event)
    else:
        db.session.delete(event)
        db.session.commit()
        return 'deleted', 204

@resource_bp.route('/events', methods=['GET', 'POST'])
@require_oauth('events')
def list_or_insert_event():
    '''Endpoint for list all the events or insert an new event.'''
    user = current_token.user
    if flask.request.method == 'GET':
        events = Event.query.filter_by(user_id=user.id).all()
        return jsonify(events)
    else:
        form = flask.request.form
        event = Event(
            user_id=user.id,
            title=form.get('title'),
            description=form.get('description'),
            time=form.get('time'),
            location=form.get('location'),
        )
        db.session.add(event)
        db.session.commit()
        return jsonify(event), 201
