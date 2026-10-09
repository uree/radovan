import redis
from flask import Flask

from app.config import Config
from app.core.providers.base_config import load_configs
from app.core.providers.base_registry import PROVIDERS
from app.logs.setup import setup_logging


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
        PROVIDERS[cfg.code_name](cfg, secrets=app.config) for cfg in configs if cfg.enabled
    ]
    try:
        app.logger.debug([n.supported_params for n in app.extensions["providers"]])
    except Exception as e:  # noqa: BLE001
        app.logger.debug(e)
    app.logger.info("Providers loaded.")
    app.logger.debug([n.code_name for n in app.extensions["providers"]])
    app.extensions["redis"] = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True,
    )

    return app