from flask import Flask, Response, make_response
from statefulauth.models import OAuth2Token
from statefulauth.serverlib import ResourceProtectorStateful, update_state, create_bearer_token_validator_stateful

from models import Event

require_oauth_stateful = ResourceProtectorStateful()
validator_stateful = create_bearer_token_validator_stateful(OAuth2Token)
require_oauth_stateful.register_token_validator(validator_stateful())

app = Flask(__name__)

@app.route('/api/events/<event_id>')
@require_oauth_stateful('events')
@update_state()
def get_event(event_id: str) -> tuple[Response, str]:
    event = Event.query.get(event_id)
    return make_response(event.as_dict), event_id