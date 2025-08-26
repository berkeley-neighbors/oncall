import logging
from falcon import HTTPFound, HTTPBadRequest
    
allow_no_auth = True

logger = logging.getLogger('oncall.auth')

def on_get(req, resp):
    logger.info("Handling auth response request")
    
    session = req.env['beaker.session']

    q_token = req.get_param('token')
        
    if q_token:
        session['accessToken'] = q_token
        session.save()
        raise HTTPFound('/')
    else:
        raise HTTPBadRequest('Invalid login attempt', 'Missing token')