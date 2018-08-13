from sanic import Blueprint
import os

URL_BASE = '/hangouts'
hangouts_event_endpoints = Blueprint('hangouts_event_endpoints')
hangouts_verification = os.getenv('CAPE_HANGOUTS_VERIFICATION', 'REPLACEME')

THIS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__)))
