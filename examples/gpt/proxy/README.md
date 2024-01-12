# Proxy
Proxy is a helper module for intgerating StatefulAuth with real-wolrd applications.
Simply use `app = get_app()` to get a Flask app with StatefulAuth integrated. Then,
register your own resource server endpoints as blueprints to the app. For example:
```
app = get_app()
app.register_blueprint(my_resource_server_bp, url_prefix="/api")
```