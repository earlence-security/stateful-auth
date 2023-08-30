import flask
from flask import Blueprint, jsonify
from authlib.integrations.flask_oauth2 import current_token

from .oauth2 import require_oauth
from .models import db, Event

resource_bp = Blueprint("resource", __name__)

# TODO: ResourceProtector.acquire_token. 
# See https://github.com/lepture/authlib/blob/master/authlib/integrations/flask_oauth2/resource_protector.py
@resource_bp.route('/me')
@require_oauth('profile')
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)

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
