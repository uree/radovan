import os
import logging


def setup_logging():
    module_dir = os.path.dirname(__file__)
    log_directory = os.path.join(module_dir, "output")
    log_file_path = os.path.join(log_directory, "radovan_core.log")

    if not os.path.exists(log_file_path):
        open(log_file_path, 'a').close()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )

    # # Check logger identity and configuration
    # print(f"Logger name: {module_logger.name}")
    # print(f"Logger level: {logging.getLevelName(module_logger.level)}")
    # print(f"Logger has handlers: {len(module_logger.handlers) > 0}")
    # print(f"Logger propagation: {module_logger.propagate}")
