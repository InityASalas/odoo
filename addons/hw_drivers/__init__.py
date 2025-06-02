# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from functools import wraps
import requests

from . import server_logger
from . import connection_manager
from . import controllers
from . import driver
from . import event_manager
from . import exception_logger
from . import http
from . import interface
from . import main
from . import websocket_client
<<<<<<< a7bbfa93410035884cd3eb8e62579f5d8faff345
from . import led_manager_L

_get = requests.get
_post = requests.post


def set_user_agent(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        headers = kwargs.pop('headers', None) or {}
        headers['User-Agent'] = 'OdooIoTBox/1.0'
        return func(*args, headers=headers, **kwargs)

    return wrapper


requests.get = set_user_agent(_get)
requests.post = set_user_agent(_post)
||||||| 01300e05d7e654d9e05f604ad320e586f54f1141
from . import led_manager_L
=======
>>>>>>> 1a83d82abbdc8508f54458cbf770fc73de7c2670
