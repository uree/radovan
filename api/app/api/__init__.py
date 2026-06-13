from flask import Blueprint


# Import blueprints
from app.api.v1_0.routes import api_1_0
from app.api.v1_1.routes import api_1_1
from app.api.v2_0.routes import api_2_0


def register_api_blueprints(app):
    app.register_blueprint(api_1_0, url_prefix='/api/v1.0')
    app.register_blueprint(api_1_1, url_prefix='/api/v1.1')
    app.register_blueprint(api_2_0, url_prefix='/api/v2.0')

