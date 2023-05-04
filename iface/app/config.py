import os
from dotenv import load_dotenv, find_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    API_CONTAINER_NAME = os.environ.get('API_CONTAINER_NAME') or 'http://localhost'
