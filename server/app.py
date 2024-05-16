import os
import sys
# add the auth-lib in our directory as path
# If using VScode, add auth-lib path to python.analysis.extraPaths in Python extension to resolve import
parent_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
auth_lib_dir = os.path.join(parent_dir, 'auth-lib')
history_lib_dir = os.path.join(parent_dir, 'historylib')
server_dir = os.path.join(parent_dir, 'server')
sys.path.append(auth_lib_dir)
sys.path.append(parent_dir)
sys.path.append(server_dir)

from website.app import create_app

cwd = os.getcwd()
app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': f'sqlite:////{cwd}/db.sqlite',
    'ENABLE_STATEFUL_AUTH': True,
    'UPLOAD_FOLDER': os.path.join(cwd, 'policies'),
    'UPDATE_PROGRAM_FOLDER': os.path.join(cwd, 'update_program'),
    'ENABLE_LOGGING': True,
    'MACAROON': False,
})
