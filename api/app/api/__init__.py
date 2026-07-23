from flask import Blueprint


# Import blueprints
from app.api.v2_0.routes import api_2_0


def register_api_blueprints(app):
    app.register_blueprint(api_2_0, url_prefix='/api/v2.0')

