from __future__ import annotations

import flask
import time
import json
from datetime import datetime
from flask import Blueprint, Response, jsonify, make_response, session
import requests

from .oauth2 import require_oauth
from .oauth2 import require_oauth_stateful
from .models import db
from authlib.integrations.flask_oauth2 import current_token

from historylib.history import History
from historylib.history_list import HistoryList
from historylib.proxy_utils import update_history_proxy

from dotenv import load_dotenv

import os

resource_bp = Blueprint("resource", __name__)

@resource_bp.route('/tok', methods=['GET'])
def tok():
    load_dotenv()
    tok = os.getenv('goog_tok')
    return tok


@resource_bp.route('/emails', methods=['GET'])
@require_oauth_stateful()
def list_emails():
    load_dotenv()
    tok = os.getenv('goog_tok')
    result = ""
    headers = {
        'Authorization': f'Bearer {tok}',
        'Accept': 'application/json',
    }
    target_api = 'https://gmail.googleapis.com/gmail/v1/users/statefulauth%40gmail.com/messages'
    response = requests.get(target_api, headers=headers)

    if response.status_code !=  403:
        response.raise_for_status()

    if response.text:
        json_object = json.loads(response.content)
        result = json.dumps(json_object, indent=2)

    return make_response(result, 201)


@resource_bp.route('/emails/<emailId>', methods=['GET'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def get_email(emailId):
    load_dotenv()
    tok = os.getenv('goog_tok')
    result = ""
    headers = {
        'Authorization': f'Bearer {tok}',
        'Accept': 'application/json',
    }
    target_api = 'https://gmail.googleapis.com/gmail/v1/users/statefulauth%40gmail.com/messages/' + emailId
    response = requests.get(target_api, headers=headers)

    if response.status_code !=  403:
        response.raise_for_status()

    if response.text:
        json_object = json.loads(response.content)
        result = json.dumps(json_object, indent=2)

    return make_response(result, 201), emailId
    