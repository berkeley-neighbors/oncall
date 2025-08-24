import logging
import requests
from oncall import db

logger = logging.getLogger(__name__)

class Authenticator:
    def __init__(self, config):
        print('Initializing Synology SSO Authenticator with config:', config)
        self.config = config
        self.import_user = config.get('auth').get('import_user', False)
        # Add more config as needed for SSO

    def authenticate(self, req):
        logger.info(f'Authenticating with Synology SSO using access token: {req}')
        session = req.env['beaker.session']
        access_token = session.get('accessToken')
        
        if not access_token:
            return False

        logger.info('Validating access token with Synology SSO provider')
        synology_config = self.config.get('synology')
        logger.debug(f'Synology Config: {synology_config}')
        sso_validate_url = synology_config.get('sso_url') + '/webman/sso/SSOAccessToken.cgi'
        app_id = synology_config.get('app_id')
        logger.debug(f'App ID: {app_id}')
        params = {
            'action': 'exchange',
            'access_token': access_token,
            'app_id': app_id
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
            if self.import_user:
                cursor.execute('INSERT INTO user (id, name, full_name, active) VALUES (%s, %s, %s, TRUE)', (user_id, user_name, user_name))
                logger.info('Imported new user from Synology SSO: %s (%s)', user_id, user_name)
                conn.commit()
            else:
                user_name = False
        
        cursor.close()
        conn.close()

        return user_name

SSO = True