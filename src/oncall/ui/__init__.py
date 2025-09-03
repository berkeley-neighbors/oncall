# -*- coding:utf-8 -*-

# Copyright (c) LinkedIn Corporation.
# All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.


import logging
import re
from ..constants import SUPPORTED_TIMEZONES, SUPPORTED_MODES
from .. import auth
from os import path, environ
from falcon import HTTPNotFound
from datetime import date
from jinja2 import FileSystemLoader
from jinja2.environment import Environment as Jinja2Environment
from webassets import Environment as AssetsEnvironment, Bundle
from webassets.ext.jinja2 import AssetsExtension
from webassets.script import CommandLineEnvironment

STATIC_ROOT = environ.get('STATIC_ROOT', path.abspath(path.dirname(__file__)))
assets_env = AssetsEnvironment(path.join(STATIC_ROOT, 'static'),
                               url='/static')

assets_env.register('libs', Bundle(
    'js/jquery-3.3.1.min.js', 'js/handlebars-4.0.12.min.js', 'js/bootstrap.min.js',
    'js/moment.js', 'js/moment-timezone.js', 'js/moment-tz-data.js',
    'js/typeahead.js', 'js/jquery.dataTables.min.js',
    output='bundles/libs.js'))
assets_env.register('oncall_js', Bundle(
    'js/navigo.js', 'js/incalendar.js', 'js/oncall.js',
    output='bundles/oncall.bundle.js'))
assets_env.register('css_libs', Bundle(
    'css/bootstrap.min.css', 'fonts/Source-Sans-Pro.css',
    'css/jquery.dataTables.min.css',
    output='bundles/libs.css'))
assets_env.register('oncall_css', Bundle(
    'css/oncall.css', 'css/incalendar.css', output='bundles/oncall.css'))
assets_env.register('loginsplash_css', Bundle(
    'css/loginsplash.css', output='bundles/loginsplash.css'))
assets_env.register('loginsplash_js', Bundle(
    'js/loginsplash.js',
    output='bundles/loginsplash.bundle.js'))

logger = logging.getLogger('webassets')

logger.addHandler(logging.StreamHandler())

jinja2_env = Jinja2Environment(extensions=[AssetsExtension], autoescape=True)
jinja2_env.loader = FileSystemLoader(path.join(STATIC_ROOT, 'templates'))
jinja2_env.assets_environment = assets_env

_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')

mimes = {
    '.css': 'text/css',
    '.jpg': 'image/jpeg',
    '.js': 'text/javascript',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ttf': 'application/octet-stream',
    '.woff': 'application/font-woff'
}


FOOTER_CONTENT = None
SLACK_INSTANCE = None
HEADER_COLOR = None
IRIS_PLAN_SETTINGS = None
TEAM_MANAGED_MESSAGE = None
SYNOLOGY_APP_ID = None
SYNOLOGY_REDIRECT_URI = None
SYNOLOGY_SDK_URL = None
SYNOLOGY_OAUTH_URL = None

def index(req, resp):
    # attempt SSO login first then default to session based login
    user = None
    if auth.auth_manager:
        user = auth.auth_manager.authenticate(req)
        
    if not user:
        user = req.env.get('beaker.session', {}).get('user')

    if user is None:
        resp.content_type = 'text/html'
        resp.text = jinja2_env.get_template('loginsplash.html').render(
            synology_sdk_url=SYNOLOGY_SDK_URL,
            oauthserver_url=SYNOLOGY_OAUTH_URL,
            synology_app_id=SYNOLOGY_APP_ID,
            redirect_uri=SYNOLOGY_REDIRECT_URI,
            nonce=req.context['nonce']
        )
    else:
        resp.content_type = 'text/html'
        resp.text = jinja2_env.get_template('index.html').render(
            user=user,
            slack_instance=SLACK_INSTANCE,
            header_color=HEADER_COLOR,
            iris_plan_settings=IRIS_PLAN_SETTINGS,
            public_calendar_base_url=PUBLIC_CALENDAR_BASE_URL,
            public_calendar_additional_message=PUBLIC_CALENDAR_ADDITIONAL_MESSAGE,
            footer=FOOTER_CONTENT,
            timezones=SUPPORTED_TIMEZONES,
            modes=SUPPORTED_MODES,
            team_managed_message=TEAM_MANAGED_MESSAGE
        )


def build_assets():
    CommandLineEnvironment(assets_env, logger).build()


def secure_filename(filename):
    for sep in path.sep, path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
        filename.split()))).strip('._')
    return filename


class StaticResource(object):
    allow_no_auth = True

    def __init__(self, path):
        self.path = path.lstrip('/')

    def on_get(self, req, resp, filename):
        suffix = path.splitext(req.path)[1]
        resp.content_type = mimes.get(suffix, 'application/octet-stream')

        filepath = path.join(STATIC_ROOT, self.path, secure_filename(filename))
        try:
            resp.stream = open(filepath, 'rb')
            resp.content_length = path.getsize(filepath)
        except IOError:
            raise HTTPNotFound()


def init(application, config):
    global SLACK_INSTANCE
    global HEADER_COLOR
    global IRIS_PLAN_SETTINGS
    global PUBLIC_CALENDAR_BASE_URL
    global PUBLIC_CALENDAR_ADDITIONAL_MESSAGE
    global TEAM_MANAGED_MESSAGE
    global SYNOLOGY_SDK_URL
    global SYNOLOGY_OAUTH_URL
    global SYNOLOGY_APP_ID
    global SYNOLOGY_REDIRECT_URI
    global FOOTER_CONTENT
    
    SLACK_INSTANCE = config.get('slack_instance')
    HEADER_COLOR = config.get('header_color', '#3a3a3a')
    IRIS_PLAN_SETTINGS = config.get('iris_plan_integration')
    PUBLIC_CALENDAR_BASE_URL = config.get('public_calendar_base_url')

    FOOTER_CONTENT = environ.get('FOOTER_CONTENT')
    SYNOLOGY_SDK_URL = environ.get('SYNOLOGY_SDK_URL')
    SYNOLOGY_OAUTH_URL = environ.get('SYNOLOGY_OAUTH_URL')
    SYNOLOGY_APP_ID = environ.get('SYNOLOGY_APP_ID')
    SYNOLOGY_REDIRECT_URI = environ.get('SYNOLOGY_REDIRECT_URI')
    
    PUBLIC_CALENDAR_ADDITIONAL_MESSAGE = config.get('public_calendar_additional_message')
    TEAM_MANAGED_MESSAGE = config.get('team_managed_message')

    application.add_sink(index, '/')
    application.add_route('/static/bundles/{filename}',
                          StaticResource('/static/bundles'))
    application.add_route('/static/images/{filename}',
                          StaticResource('/static/images'))
    application.add_route('/static/fonts/{filename}',
                          StaticResource('/static/fonts'))
