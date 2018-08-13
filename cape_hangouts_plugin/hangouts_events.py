import json
import re
from collections import deque
from hashlib import sha256

from external_integration_hangouts.hangouts_settings import URL_BASE, hangouts_verification
from external_integration_hangouts.hangouts_settings import hangouts_event_endpoints
from webservices.bots_common.utils import process_action
from webservices.app.app_middleware import respond_with_plain_json, requires_auth
from logging import debug, warning
from userdb.hangouts_space import HangoutsSpace
from userdb.user import User
from api_helpers.input import required_parameter
from sanic.response import redirect

_endpoint_route = lambda x: hangouts_event_endpoints.route(URL_BASE + x, methods=['GET', 'POST'])

_processed_events = deque(maxlen=1000)


def process_message(user, space, request, message):
    message = re.sub("@capebot", "", message, flags=re.I).strip()
    response = process_action(user, space.space_id, request, message)
    if response is not None:
        return response
    else:
        return {'text': 'Sorry, I had a problem doing that.'}


def process_new_space(space):
    return {"text": "Hi! To get started, associate this room with the Cape account you'd like me to use.",
            "cards": [
                {
                "sections": [
                    {
                        "widgets": [
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "Associate Account",
                                            "onClick": {
                                                "openLink": {
                                                    "url": f'https://ui-thermocline.thecape.ai/authentication.html?configuration=%7B"authentication":%7B"login":%7B"redirectURL":"https://hangouts.thecape.ai/hangouts/associate?space={space}"%7D%7D%7D#/'
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }


@_endpoint_route('/associate')
@requires_auth
def associate(request):
    space_id = required_parameter(request, 'space')
    space = HangoutsSpace()
    space.user_id = request['user'].user_id
    space.space_id = space_id
    space.save()
    return redirect('https://thecape.ai/hangouts.html')


# Google requires the endpoint to be a random string
@_endpoint_route('/A4invdjknViuhwefoijadsf')
@respond_with_plain_json
def receive_event(request):
    debug("Hangouts args: " + str(request['args']))
    token = required_parameter(request, 'token')
    type = required_parameter(request, 'type')
    if token != hangouts_verification:
        return {"success": False, "message": "Invalid token"}
    # Google doesn't provide an ID, so we use a hash of the event to check for already processed events
    event_id = sha256(str(request['args']).encode('utf-8'))
    space_id = json.loads(required_parameter(request, 'space'))['name']
    if event_id in _processed_events:
        # We've already processed this event
        return {"success": True}
    _processed_events.append(event_id)
    if type == 'ADDED_TO_SPACE':
        return process_new_space(space_id)
    elif type == 'MESSAGE':
        space = HangoutsSpace.get('space_id', space_id)
        if space is None:
            return process_new_space(space_id)
        user = User.get('user_id', space.user_id)
        message = json.loads(required_parameter(request, 'message'))['text']
        response = process_message(user, space, request, message)
        return response
    else:
        warning("Unsupported hangouts message")
        return {"success": False}
