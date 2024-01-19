from flask import session
from .models import User

def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None


def split_by_crlf(s):
    import re
    regex_pattern = '|'.join(map(re.escape, ['\r\n', '\r', '\n', ',', ';', ' ']))
    return list(filter(lambda x: x != '', re.split(regex_pattern, s)))