import logging
import requests
from oncall import db
from os import environ

logger = logging.getLogger(__name__)

class Authenticator:
    def __init__(self, config):
        self.config = config

    def authenticate(self, req):
        logger.info(f'Authenticating with Synology SSO using access token: {req}')
        session = req.env['beaker.session']
        access_token = session.get('accessToken')
        
        if not access_token:
            return False

        logger.debug('Validating access token with Synology SSO provider')
        SYNOLOGY_APP_ID = environ.get('SYNOLOGY_APP_ID')
        SYNOLOGY_OAUTH_URL = environ.get('SYNOLOGY_OAUTH_URL')
        sso_validate_url = SYNOLOGY_OAUTH_URL + '/webman/sso/SSOAccessToken.cgi'
        logger.debug(f'App ID: {SYNOLOGY_APP_ID}')
        
        params = {
            'action': 'exchange',
            'access_token': access_token,
            'app_id': SYNOLOGY_APP_ID
        }
        logger.debug('Sending request to Synology SSO validate URL: %s with params: %s', sso_validate_url, params)
        resp = requests.get(sso_validate_url, params=params)
        resp.raise_for_status()
        logger.info('Received response from Synology SSO: %s', resp.text)
        data = resp.json()
        if not data.get('success'):
            logger.error('Synology SSO token validation failed: %s', data)
            return False
        
        user_id = data.get('data', {}).get('user_id')
        user_name = data.get('data', {}).get('user_name')
        if not user_id or not user_name:
            logger.error('Missing user_id or user_name in Synology SSO response')
            return False

        logger.info('User ID: %s, User Name: %s', user_id, user_name)
        conn = db.connect()
        cursor = conn.cursor(db.DictCursor)
        cursor.execute('SELECT name FROM user WHERE id = %s', (user_id,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute('INSERT INTO user (id, name, full_name, active) VALUES (%s, %s, %s, TRUE)', (user_id, user_name, user_name))
            logger.info('Imported new user from Synology SSO: %s (%s)', user_id, user_name)
            conn.commit()
            cursor.execute('INSERT INTO `user_contact` (`user_id`, `mode_id`, `destination`) VALUES (%s, %s, %s)', (user_id, 1, ''))
            cursor.execute('INSERT INTO `user_contact` (`user_id`, `mode_id`, `destination`) VALUES (%s, %s, %s)', (user_id, 2, ''))
            cursor.execute('INSERT INTO `user_contact` (`user_id`, `mode_id`, `destination`) VALUES (%s, %s, %s)', (user_id, 3, ''))
            conn.commit()

        cursor.close()
        conn.close()

        return user_name

SSO = True