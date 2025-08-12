# -*- coding: utf-8 -*-

from flask import Blueprint, session, redirect, url_for, request
import google_auth_oauthlib.flow

from ..config import AppConfig
from ..utils.auth_utils import credentials_to_dict


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        AppConfig.GOOGLE_CLIENT_SECRETS_FILE, scopes=AppConfig.YT_SCOPES)
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)


@auth_bp.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        AppConfig.GOOGLE_CLIENT_SECRETS_FILE, scopes=AppConfig.YT_SCOPES, state=state)
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('index'))


@auth_bp.route('/logout')
def logout():
    if 'credentials' in session:
        del session['credentials']
    return redirect(url_for('index'))
