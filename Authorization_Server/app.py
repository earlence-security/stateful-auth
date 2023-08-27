import os
import sys
# add the auth-lib in our directory as path
# If using VScode, add auth-lib path to python.analysis.extraPaths in Python extension to resolve import
parent_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
auth_lib_dir = os.path.join(parent_dir, 'auth-lib')
sys.path.append(auth_lib_dir)

from website.app import create_app


app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite',
    'ENABLE_STATEFUL_AUTH': False,
})
