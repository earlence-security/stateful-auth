import os
import sys

from os.path import abspath, dirname, join

# Replace authlib with our own `auth-lib`.
# add the auth-lib in our directory as path
# If using VScode, add auth-lib path to python.analysis.extraPaths in Python extension to resolve import
parent_dir = abspath(dirname(dirname(dirname(__file__))))
parent_dir = abspath(join(parent_dir, os.pardir))
auth_lib_dir = join(parent_dir, 'auth-lib')
sys.path.append(auth_lib_dir)
sys.path.append(parent_dir)

from proxy.app import create_app
from examples.joplin.server.resource_routes import resource_bp, init_server_api

cwd = os.getcwd()
app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': f'sqlite:////{cwd}/db.sqlite',
    'ENABLE_STATEFUL_AUTH': True,
    'UPLOAD_FOLDER': os.path.join(cwd, 'policies'),
})

init_server_api(app)
app.register_blueprint(resource_bp, url_prefix="/api")
