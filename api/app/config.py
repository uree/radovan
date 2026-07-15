import os

from dotenv import load_dotenv


load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    RESTFUL_JSON = {"ensure_ascii": False}
    AAAAARG_USER = os.environ.get("YARR_USER", None)
    AAAAARG_PASS = os.environ.get("YARR_PASS", None)
    LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", "DEBUG")
    OADOI_EMAIL = os.environ.get("OADOI_EMAIL", None)