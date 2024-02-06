from requests import get, Request
from statefulauth.clientlib import attach_state, store_state

def send(req: Request, obj_id: str):
    req = attach_state(req, obj_id)
    resp = get(req)
    store_state(resp, obj_id)