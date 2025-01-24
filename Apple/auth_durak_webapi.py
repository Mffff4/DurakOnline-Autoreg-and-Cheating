from requests import Session
from xeger import xeger


class AuthDurakWebApi:
    def __init__(self, email, password, apple_fingerprint):
        self.session = Session()
        self.apple_fingerprint = apple_fingerprint
        self.session.headers['X-Apple-I-FD-Client-Info'] = apple_fingerprint
        self.session.headers['User-Agent'] = self.session.headers['X-Apple-I-FD-Client-Info'].split('"U":"')[1].split('"')[0]
        self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self.email = email
        self.password = password
        self.x_apple_widget_key = None
        self.x_apple_auth_attributes = None
        self.x_apple_id_session_id = None
        self.x_apple_frame_id = None

    def update_x_apple_frame_id(self):
        self.x_apple_frame_id = xeger(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        self.session.headers['X-Apple-Frame-Id'] = self.x_apple_frame_id

    def auth_authorize(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': 'https://durak.rstgames.com/',
        }
        params = {
            'client_id': 'com.rstgames.durak.sid',
            'redirect_uri': 'https://durak.rstgames.com/auth/apple_cb',
            'response_type': 'code id_token',
            'state': 'state',
            'scope': 'name email',
            'response_mode': 'form_post',
            'X-Apple-Frame_Id': self.x_apple_frame_id,
            'm': '22',
            'v': '1.5.5',
        }
        auth_authorize_response = self.session.get('https://appleid.apple.com/auth/authorize', params=params, headers=headers)
        return auth_authorize_response

    def update_x_apple_widget_key(self, auth_authorize_response):
        x_apple_widget_key = auth_authorize_response.text.split('"authServiceKey":"')[1].split('"')[0]
        self.x_apple_widget_key = x_apple_widget_key
        self.session.headers['X-Apple-Widget-Key'] = x_apple_widget_key

    def update_x_apple_auth_attributes(self, auth_authorize_response):
        x_apple_auth_attributes = auth_authorize_response.headers.get('X-Apple-Auth-Attributes')
        self.x_apple_auth_attributes = x_apple_auth_attributes
        self.session.headers['X-Apple-Auth-Attributes'] = x_apple_auth_attributes

    # Good status_response = 200
    def auth_federate(self):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
        }
        params = {
            'isRememberMeEnabled': 'false',
        }
        json_data = {
            'accountName': self.email,
            'rememberMe': False,
        }
        auth_federate_response = self.session.post('https://appleid.apple.com/appleauth/auth/federate', params=params, headers=headers, json=json_data)
        return auth_federate_response

    def signin_init(self, auth_federate_response, a):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/json',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'Scnt': auth_federate_response.headers.get('Scnt'),
        }
        json_data = {
            'a': a,
            'accountName': self.email,
            'protocols': [
                's2k',
                's2k_fo',
            ],
        }
        response_signin_init = self.session.post('https://appleid.apple.com/appleauth/auth/signin/init', headers=headers, json=json_data)
        return response_signin_init

    def signin_complete(self, response_signin_init, m1, c, m2):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/json',
            'Origin': 'https://appleid.apple.com',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'scnt': response_signin_init.headers.get('Scnt'),
        }
        params = {
            'isRememberMeEnabled': 'false',
        }
        json_data = {
            'accountName': self.email,
            'rememberMe': False,
            'm1': m1,
            'c': c,
            'm2': m2,
        }
        response_signin_complete = self.session.post('https://appleid.apple.com/appleauth/auth/signin/complete', params=params, headers=headers, json=json_data)
        return response_signin_complete

    def update_x_apple_id_session_id(self, response_signin_complete):
        x_apple_id_session_id = response_signin_complete.headers.get('X-Apple-ID-Session-Id')
        self.x_apple_id_session_id = x_apple_id_session_id
        self.session.headers['X-Apple-ID-Session-Id'] = x_apple_id_session_id

    def appleauth_auth(self, response_signin_complete):
        headers = {
            'Accept': 'text/html',
            'Content-Type': 'application/json',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'scnt': response_signin_complete.headers.get('Scnt'),
        }
        response_auth_hsa2 = self.session.get('https://appleid.apple.com/appleauth/auth', headers=headers)
        return response_auth_hsa2

    def phone_securitycode(self, response_auth_hsa2, code):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'scnt': response_auth_hsa2.headers.get('Scnt'),
        }
        json_data = {
            'phoneNumber': {
                'id': 1,
            },
            'securityCode': {
                'code': code,
            },
            'mode': 'sms',
        }
        response_securitycode = self.session.post('https://appleid.apple.com/appleauth/auth/verify/phone/securitycode', headers=headers, json=json_data)
        return response_securitycode

    # Good status_code = 204
    def auth_2sv_trust(self, response_securitycode):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/json',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'scnt': response_securitycode.headers.get('Scnt'),
        }
        response_2sv_trust = self.session.get('https://appleid.apple.com/appleauth/auth/2sv/trust', headers=headers)
        return response_2sv_trust

    # Good status_code = 200
    def oauth_consent(self, response_2sv_trust):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/json',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'scnt': response_2sv_trust.headers.get('Scnt'),
        }
        params = {
            'client_id': 'com.rstgames.durak.sid',
            'redirect_uri': 'https://durak.rstgames.com/auth/apple_cb',
            'response_type': 'code id_token',
            'state': 'state',
            'scope': 'name email',
            'response_mode': 'form_post',
            'frame_id': self.x_apple_frame_id,
            'm': '22',
            'v': '1.5.5',
        }
        response_oauth_consent = self.session.get('https://appleid.apple.com/appleauth/auth/oauth/consent', params=params, headers=headers)
        return response_oauth_consent

    # Good status_code = 200
    def consent_complete(self, response_oauth_consent):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/json',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Consent': response_oauth_consent.headers.get('X-Apple-Oauth-Consent'),
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'X-Requested-With': 'XMLHttpRequest',
            'scnt': response_oauth_consent.headers.get('Scnt'),
        }
        response_consent_complete = self.session.put('https://appleid.apple.com/appleauth/auth/oauth/consent/complete', headers=headers)
        return response_consent_complete

    # Good status_code = 200
    def oauth_authorize(self, response_consent_complete):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Apple-OAuth-Client-Id': 'com.rstgames.durak.sid',
            'X-Apple-OAuth-Client-Type': 'thirdPartyAuth',
            'X-Apple-OAuth-Consent': response_consent_complete.headers.get('X-Apple-Oauth-Consent'),
            'X-Apple-OAuth-Redirect-URI': 'https://durak.rstgames.com/auth/apple_cb',
            'X-Apple-OAuth-Require-Grant-Code': 'true',
            'X-Apple-OAuth-Response-Mode': 'form_post',
            'X-Apple-OAuth-Response-Type': 'code id_token',
            'X-Apple-OAuth-Scopes': 'name email',
            'X-Apple-OAuth-State': 'state',
            'X-Apple-Privacy-Consent': 'true',
            'X-Apple-Widget-Key': self.x_apple_widget_key,
            'X-Requested-With': 'XMLHttpRequest',
            'scnt': response_consent_complete.headers.get('Scnt'),
        }
        json_data = {
            'client': {
                'id': 'com.rstgames.durak.sid',
                'redirectUri': 'https://durak.rstgames.com/auth/apple_cb',
            },
            'scopes': [],
            'state': 'state',
            'anonymousEmail': False,
            'responseMode': 'form_post',
            'responseType': 'code id_token',
        }
        oauth_authorize_response = self.session.post(
            'https://appleid.apple.com/appleauth/auth/oauth/authorize',
            headers=headers,
            json=json_data,
        )
        return oauth_authorize_response
