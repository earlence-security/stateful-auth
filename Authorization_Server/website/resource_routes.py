import flask
import time
from datetime import datetime
from flask import Blueprint, jsonify, make_response
from authlib.integrations.flask_oauth2 import current_token
import json

from authlib.integrations.flask_oauth2 import current_token
from .oauth2 import require_oauth
from .oauth2 import require_oauth_stateful
from .models import db, Event, Email

from historylib.history import History
from historylib.history_list import HistoryList
from historylib.server_utils import update_history


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


@resource_bp.route('/emails/<uuid:emailId>', methods=['GET', 'DELETE'])
@require_oauth_stateful()
@update_history(session=db.session)
def get_or_delete_emails(emailId):
    '''Endpoint for get or delete an email.'''
    user = current_token.user
    email = Email.query.filter_by(id=emailId).first()
    historylist_json = flask.request.headers.get('Authorization-History')
    historylist = HistoryList(historylist_json)

    # If the event does not belong to the current user, abort.
    if not email:
        # Bad request
        make_response('bad request', 400)
    if email.user_id != user.id:
        # Forbidden
        make_response('forbidden', 403)
    if flask.request.method == 'GET':
        # TODO 
        # make it into function
        resp = make_response(jsonify(email.as_dict))
        return resp
    else:
        db.session.delete(email)
        db.session.commit()
        return make_response('deleted', 204)

@resource_bp.route('/emails', methods=['GET', 'POST'])
@require_oauth_stateful()
@update_history(session=db.session)
def list_or_insert_email():
    '''Endpoint for list all the email or insert an new email.'''
    user = current_token.user
    if flask.request.method == 'GET':
        emails = Email.query.filter_by(user_id=user.id).all()
        email_json = []
        for email in emails:
            this_dict = email.as_dict
            # email_json.append({'id': this_dict['id']})
            email_json.append(this_dict)
        return make_response(jsonify(user_id=user.id, results=email_json))
    else:
        email_request = flask.request.get_json()
        email = Email(
            user_id=user.id,
            title=email_request.get('title'),
            content=email_request.get('content'),
        )
        db.session.add(email)
        db.session.commit()
        resp = make_response(jsonify(email.as_dict), 201)
        return resp


@resource_bp.route('/events/<uuid:eventId>', methods=['GET', 'DELETE'])
@require_oauth('profile')  # TODO: Replace scope w/ other value (eg. "events")
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
        return jsonify(event.as_dict)
    else:
        db.session.delete(event)
        db.session.commit()
        return 'deleted', 204

@resource_bp.route('/events', methods=['GET', 'POST'])
@require_oauth('profile')  # TODO: Replace scope w/ other value (eg. "events")
def list_or_insert_event():
    '''Endpoint for list all the events or insert an new event.'''
    user = current_token.user
    if flask.request.method == 'GET':
        events = Event.query.filter_by(user_id=user.id).all()
        return jsonify([(e.as_dict) for e in events])
    else:
        form = flask.request.form
        if 'date' in form:
            try:
                t = datetime.fromisoformat(form.get('time')).timestamp()
            except:
                # Bad request
                return "Invalid time format. Please use ISO format.", 400
        else:
            t = time.time()
        event = Event(
            user_id=user.id,
            name=form.get('name', default='(No title)'),
            description=form.get('description', default=''),
            time=t,
            location=form.get('location', default=''),
        )
        db.session.add(event)
        db.session.commit()
        print(event.as_dict)
        return jsonify(event.as_dict), 201
