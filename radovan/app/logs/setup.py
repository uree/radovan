import os
import logging
import logging.config


# def setup_logging():
#     """Set up logging for development or production based on the ENV env var."""
#     log_configs = {
#         "dev": "logging.dev.ini",
#         "stg": "logging.dev.ini",
#         "prod": "logging.prod.ini"
#     }
#     config = log_configs.get(os.environ["ENV"], "logging.dev.ini")
#     config_path = "/".join([os.environ["LOG_CONFIG_DIR"], config])
#     print(config_path)

#     # defaults
#     log_output_dir = os.environ["LOG_OUTPUT_DIR"]
#     log_file_path = os.path.join(log_output_dir, "main.log")
#     print(log_file_path)

#     os.makedirs(log_output_dir, exist_ok=True)
#     if not os.path.exists(log_file_path):
#         open(log_file_path, 'a').close()

#     logging.config.fileConfig(
#         config_path,
#         disable_existing_loggers=False,
#         defaults={"logfilename": f"{log_file_path}"},
#     )


def setup_logging(level="INFO"):
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {
            "handlers": ["default"],
            "level": "INFO",
        },
    }

    logging.config.dictConfig(config)