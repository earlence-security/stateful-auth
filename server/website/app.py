import os
from flask import Flask, g

from .models import db
from .oauth2 import config_oauth
from .auth_routes import auth_bp


def create_app(config=None):
    app = Flask(__name__)
    app.logger.setLevel('DEBUG')
    # load default configuration
    app.config.from_object('website.settings')

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    setup_app(app)
    return app


def setup_app(app):

    db.init_app(app)
    # Create tables if they do not exist already
    with app.app_context():
        db.create_all()
    config_oauth(app)
    if not app.config.get('EVAL'):
        from .resource_routes import resource_bp
    elif app.config.get('ENABLE_STATEFUL_AUTH'):
        from .resource_routes_eval import resource_bp
    else:
        from .resource_routes_eval_baseline import resource_bp

    app.register_blueprint(auth_bp, url_prefix='')
    app.register_blueprint(resource_bp, url_prefix="/api")

    # Create upload folder if it does not exist already
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
