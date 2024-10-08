from __future__ import annotations

import flask
import time
import atexit
import json
from uuid import UUID
from datetime import datetime
from flask import Blueprint, Response, jsonify, make_response, current_app, request, g

from .oauth2 import require_oauth
from .oauth2 import require_oauth_stateful
from .models import db, Event, Email
from authlib.integrations.flask_oauth2 import current_token

from historylib.history import History
from historylib.history_list import HistoryList
from historylib.server_utils import update_history
from utils.log import RequestLog, LogManager


resource_bp = Blueprint("resource", __name__)

# Create a log manager for microbenchmarking, and store it in the app context.
global_log_manager = LogManager()
def save_logs():
    # global_log_manager.print_all_logs()
    global_log_manager.to_file()
atexit.register(save_logs)

# Register before_request hook for all the routes in this blueprint.
# This hook will be called before every request to this blueprint.
@resource_bp.before_request
def create_request_log():
    """Create a request log for the current request."""
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING']:
        g.current_log = RequestLog(
            request_path=request.path,
            request_method=request.method,
        )
        g.current_log.request_total_time = time.time()


# Register after_request hook for all the routes in this blueprint.
# This hook will be called after every request to this blueprint.
@resource_bp.after_request
def update_history_list(response: Response) -> Response:
    """Update the history list of the current object."""
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        current_log = g.current_log
        response_data_size = len(response.data)
        current_log.response_data_size = response_data_size
        current_log.request_total_time = time.time() - current_log.request_total_time
        # print(f"[LOGGING] {current_log}")
        # Append to the global log manager.
        global_log_manager.add_log(current_log)
    return response


# TODO: ResourceProtector.acquire_token. 
# See https://github.com/lepture/authlib/blob/master/authlib/integrations/flask_oauth2/resource_protector.py
@resource_bp.route('/me')
@require_oauth('profile')
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username, message="Hello World!")


# Dummy api to demonstrate stateless policies
@resource_bp.route('/me2')
@require_oauth('profile')
def api_me2():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)


# Another Dummy api to demonstrate stateless policies
@resource_bp.route('/send-money', methods=['POST'])
@require_oauth('profile')
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
@require_oauth('profile')
def get_or_delete_emails(emailId: UUID) -> Response | tuple[Response, UUID | list[UUID]]:
    '''Endpoint for get or delete an email.'''
    user = current_token.user
    email = Email.query.filter_by(id=emailId).first()

    # If the event does not belong to the current user, abort.
    if not email:
        # Bad request
        return make_response('bad request', 400)
    if email.user_id != user.id:
        # Forbidden
        return make_response('forbidden', 403)
    if flask.request.method == 'GET':
        resp = make_response(jsonify(email.as_dict))
        return resp, email.id
    else:
        db.session.delete(email)
        db.session.commit()
        return make_response('deleted', 204), email.id

@resource_bp.route('/emails', methods=['GET', 'POST'])
@require_oauth('profile')
def list_or_insert_email() -> Response | tuple[Response, UUID | list[UUID]]:
    '''Endpoint for list all the email or insert an new email.'''
    user = current_token.user
    if flask.request.method == 'GET':
        emails = Email.query.filter_by(user_id=user.id).all()
        email_json = []
        for email in emails:
            this_dict = email.as_dict
            email_json.append({'id': this_dict['id']})
            #email_json.append(this_dict)
        resp = make_response(jsonify(user_id=user.id, results=email_json))
        return resp
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
        return resp, email.id
    
@resource_bp.route('/emails/batch-get', methods=['GET', 'POST'])
@require_oauth('profile')
def batch_get_email() -> Response | tuple[Response, UUID | list[UUID]]:
    '''Endpoint for list all the email or insert an new email.'''
    user = current_token.user
    if flask.request.method == 'POST':
        user = current_token.user
        req = flask.request.get_json()
        email_ids = req.get('ids')
        ret_emails = []
        ret_emials_dicts = []
        for emailId in email_ids:
            emailId = UUID(emailId)
            email = Email.query.filter_by(id=emailId).first()
            # If the event does not belong to the current user, abort.
            if email and email.user_id == user.id:
                ret_emails.append(email)
                ret_emials_dicts.append(email.as_dict)
        resp = make_response(jsonify(user_id=user.id, results=ret_emials_dicts))
        return resp, [e.id for e in ret_emails]
    

# Google Calendar Endpoints but doing nothing. 
@resource_bp.route('/events/<uuid:eventId>', methods=['GET', 'DELETE', 'POST', 'PATCH', 'PUT'])
@require_oauth('profile')
def get_or_delete_event(eventId: UUID) -> Response | tuple[Response, UUID | list[UUID]]:
    user = current_token.user
    event = Event(
        id=UUID(eventId),
        user_id=user.id,
    )
    db.session.add(event)
    db.session.commit()
    return make_response(jsonify(event.as_dict))

@resource_bp.route('/events/import', methods=['POST'])
@require_oauth('profile')
def import_events() -> Response | tuple[Response, UUID | list[UUID]]:
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        resource_api_start = time.time()
    ids = [UUID(id) for id in json.loads(flask.request.data).get('ids')]
    user = current_token.user
    for id in ids:
        event = Event(
            id=id,
            user_id=user.id,
        )
        db.session.add(event)
    db.session.commit()
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        current_log = g.current_log
        current_log.resource_api_time = time.time() - resource_api_start
    return make_response(jsonify({'ids': ids}))

@resource_bp.route('/events', methods=['POST', 'GET'])
@require_oauth('profile')
def create_events() -> Response | tuple[Response, UUID | list[UUID]]:
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        resource_api_start = time.time()
    ids = [UUID(id) for id in json.loads(flask.request.data).get('ids')]
    user = current_token.user
    for id in ids:
        event = Event(
            id=id,
            user_id=user.id,
        )
        db.session.add(event)
    db.session.commit()
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        current_log = g.current_log
        current_log.resource_api_time = time.time() - resource_api_start
    return make_response(jsonify({'ids': ids}))

@resource_bp.route('/events/<uuid:eventId>/instances', methods=['GET'])
@require_oauth('profile')
def list_event_instances(eventId:UUID) -> Response | tuple[Response, UUID | list[UUID]]:
    user = current_token.user
    event = Event(
        id=UUID(eventId),
        user_id=user.id,
    )
    db.session.add(event)
    db.session.commit()
    return make_response(jsonify(event.as_dict))

@resource_bp.route('/events/<uuid:eventId>/move', methods=['POST'])
@require_oauth('profile')
def move_event(eventId:UUID) -> Response | tuple[Response, UUID | list[UUID]]:
    user = current_token.user
    event = Event(
        id=UUID(eventId),
        user_id=user.id,
    )
    db.session.add(event)
    db.session.commit()
    return make_response(jsonify(event.as_dict))

@resource_bp.route('/events/quickAdd', methods=['POST'])
@require_oauth('profile')
def quick_add_event() -> Response | tuple[Response, UUID | list[UUID]]:
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        resource_api_start = time.time()

    ids = [UUID(id) for id in json.loads(flask.request.data).get('ids')]
    user = current_token.user
    for id in ids:
        event = Event(
            id=id,
            user_id=user.id,
        )
        db.session.add(event)
    db.session.commit()
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        current_log = g.current_log
        current_log.resource_api_time = time.time() - resource_api_start
    return make_response(jsonify({'ids': ids}))

@resource_bp.route('/events/watch', methods=['POST'])
@require_oauth('profile')
def watch() -> Response | tuple[Response, UUID | list[UUID]]:
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        resource_api_start = time.time()

    ids = [UUID(id) for id in json.loads(flask.request.data).get('ids')]
    user = current_token.user
    for id in ids:
        event = Event(
            id=id,
            user_id=user.id,
        )
        db.session.add(event)
    db.session.commit()
    # LOGGING
    if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
        and hasattr(g, 'current_log'):
        current_log = g.current_log
        current_log.resource_api_time = time.time() - resource_api_start
    return make_response(jsonify({'ids': ids}))
