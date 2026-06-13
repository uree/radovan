import redis

from flask import Flask

from app.config import Config
from app.logs.setup import setup_logging
# from app.core.providers.aaaaarg import arglogin
from app.core.providers.base_registry import PROVIDERS
from app.core.providers.base_config import load_configs


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    setup_logging(level=app.config["LOGGING_LEVEL"])
    app.logger.info("Error logging works.")
    app.logger.debug("Error logging works.")

    from app.api import register_api_blueprints
    register_api_blueprints(app)

    configs = load_configs()
    app.extensions["providers"] = [
        PROVIDERS[cfg.code_name](cfg) for cfg in configs if cfg.enabled
    ]
    app.logger.info("Providers loaded.")
    app.logger.debug([n.code_name for n in app.extensions["providers"]])
    app.extensions["redis"] = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True,
    )

    # arglogin
    # if app.config["AAAARAG_ON"]:
    #     try:
    #         app.logger.debug("Creating arg browser ...")
    #         app.aaaaarg_browser = arglogin(app.config["AAAAARG_USER"], app.config["AAAAARG_PASS"])
    #     except AttributeError:
    #         app.aaaaarg_browser = None

    return app