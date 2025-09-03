# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from ... import db
from ujson import dumps as json_dumps
from os import environ

mode_to_name = {
    'email': 'Email',
    'sms': 'SMS',
    'call': 'Phone Call',
    'slack': 'Slack',
    'teams_messenger': 'Teams Messenger'
}

def on_get(req, resp):
    """
    Get all contact modes
    """
    connection = db.connect()
    cursor = connection.cursor()
    cursor.execute('SELECT `name` FROM `contact_mode`')
    supported_modes = ' '.join(environ.get('SUPPORTED_MODES').split(','))
    data = [row[0] for row in cursor if row[0] in supported_modes]
    cursor.close()
    connection.close()
    resp.body = json_dumps([{'mode': item, 'name': mode_to_name[item]} for item in data])
