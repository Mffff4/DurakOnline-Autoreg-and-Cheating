import hashlib

import psutil
from requests import Session
from rstr import xeger


class WebAPI:
    def __init__(self, email, password, phone_number, first_name, last_name, country_code_1, country_code_2, apple_fingerprint):
        self.session = Session()
        self.apple_fingerprint = apple_fingerprint
        self.session.headers['X-Apple-I-FD-Client-Info'] = apple_fingerprint
        self.session.headers['User-Agent'] = self.session.headers['X-Apple-I-FD-Client-Info'].split('"U":"')[1].split('"')[0]
        self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self.email = email
        self.password = password
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.client_id = None
        self.widget_key = None
        self.country_code_1 = country_code_1
        self.country_code_2 = country_code_2

    @staticmethod
    def close_captcha_window():
        procs = psutil.process_iter()
        for proc in procs:
            name = proc.name()
            if name == "PhotosApp.exe":
                proc.kill()

    def update_client_id(self) -> str:
        self.client_id = xeger(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        return self.client_id

    def update_widget_key(self):
        headers = {
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.icloud.com/',
        }
        params = {
            'clientBuildNumber': '2420Hotfix12',
            'clientMasteringNumber': '2420Hotfix12',
            'clientId': self.client_id,
        }
        validate_response = self.session.post('https://setup.icloud.com/setup/ws/1/validate', params=params,
                                              headers=headers)
        self.widget_key = validate_response.text.split('widgetKey=')[1].split('#!create')[0]
        self.session.headers.update({
            'X-Apple-Widget-Key': self.widget_key
        })
        return self.widget_key

    def widget_account(self):
        headers = {
            'Referer': 'https://www.icloud.com/',
        }
        params = {
            'widgetKey': self.widget_key,
            'locale': 'ru_RU',
        }
        widget_account_response = self.session.get('https://appleid.apple.com/widget/account/',
                                                   headers=headers,
                                                   params=params)
        return widget_account_response

    def captcha(self, widget_account_response):
        headers = {
            'scnt': widget_account_response.headers.get('scnt')
        }
        json_data = {
            'type': 'IMAGE',
        }
        captcha_response = self.session.post('https://appleid.apple.com/captcha', headers=headers, json=json_data)
        return captcha_response

    def account_validate(self, x_apple_hc, captcha_response, captcha_id, captcha_token, captcha_answer):
        headers = {
            'X-APPLE-HC': x_apple_hc,
            'scnt': captcha_response.headers.get('scnt'),
        }
        json_data = {
            'account': {
                'name': self.email,
                'password': self.password,
                'person': {
                    'name': {
                        'firstName': self.first_name,
                        'lastName': self.last_name,
                    },
                    'birthday': '2000-01-01',
                    'primaryAddress': {
                        'country': 'RUS',
                    },
                },
                'preferences': {
                    'preferredLanguage': 'ru_RU',
                    'marketingPreferences': {
                        'appleNews': False,
                        'appleUpdates': True,
                        'iTunesUpdates': True,
                    },
                },
                'verificationInfo': {
                    'id': '',
                    'answer': '',
                },
            },
            'captcha': {
                'id': captcha_id,
                'token': captcha_token,
                'answer': captcha_answer,
            },
            'phoneNumberVerification': {
                'phoneNumber': {
                    'id': 1,
                    'number': self.phone_number,
                    'countryCode': self.country_code_2,
                    'countryDialCode': '',
                    'nonFTEU': False,
                },
                'mode': 'sms',
            },
            'privacyPolicyChecked': False,
        }
        account_validate_response = self.session.post('https://appleid.apple.com/account/validate', headers=headers,
                                                      json=json_data)
        return account_validate_response

    # Good response = 201
    def account_verification_post(self, account_validate_response):
        headers = {
            'scnt': account_validate_response.headers.get('scnt'),
        }
        json_data = {
            'account': {
                'name': self.email,
                'person': {
                    'name': {
                        'firstName': self.first_name,
                        'lastName': self.last_name,
                    },
                },
            },
            'countryCode': self.country_code_1,
        }
        account_verification_response = self.session.post('https://appleid.apple.com/account/verification',
                                                          headers=headers, json=json_data)
        return account_verification_response

    def account_verification_put(self, account_verification_response, verification_id, verification_email_answer):
        headers = {
            'scnt': account_verification_response.headers.get('scnt'),
        }
        json_data = {
            'name': self.email,
            'verificationInfo': {
                'id': verification_id,
                'answer': verification_email_answer,
            },
        }
        account_verification_response = self.session.put('https://appleid.apple.com/account/verification',
                                                         headers=headers, json=json_data)
        return account_verification_response

    def verification_phone_post(self, x_apple_hc, account_verification_response, verification_id, verification_email_answer):
        headers = {
            'X-APPLE-HC': x_apple_hc,
            'scnt': account_verification_response.headers.get('scnt'),
        }
        json_data = {
            'phoneNumberVerification': {
                'phoneNumber': {
                    'id': 1,
                    'number': self.phone_number,
                    'countryCode': self.country_code_2,
                    'countryDialCode': '',
                    'nonFTEU': False,
                },
                'securityCode': {
                    'code': '',
                },
                'mode': 'sms',
            },
            'account': {
                'name': self.email,
                'password': self.password,
                'person': {
                    'name': {
                        'firstName': self.first_name,
                        'lastName': self.last_name,
                    },
                    'birthday': '2000-01-01',
                    'primaryAddress': {
                        'country': 'RUS',
                    },
                },
                'verificationInfo': {
                    'id': verification_id,
                    'answer': verification_email_answer,
                },
                'preferences': {
                    'preferredLanguage': 'ru_RU',
                    'marketingPreferences': {
                        'appleNews': False,
                        'appleUpdates': True,
                        'iTunesUpdates': True,
                    },
                },
            },
            'privacyPolicyChecked': None,
        }
        verification_phone_response = self.session.post('https://appleid.apple.com/account/verification/phone',
                                                        headers=headers, json=json_data)
        return verification_phone_response

    # 201
    def verification_phone_put(self, verification_phone_response, security_code, verification_id, verification_email_answer):
        headers = {
            'scnt': verification_phone_response.headers.get('scnt'),
        }
        json_data = {
            'phoneNumberVerification': {
                'phoneNumber': {
                    'id': 1,
                    'number': self.phone_number,
                    'countryCode': self.country_code_2,
                    'countryDialCode': '',
                    'nonFTEU': False,
                },
                'securityCode': {
                    'code': security_code,
                },
                'mode': 'sms',
            },
            'account': {
                'name': self.email,
                'password': self.password,
                'person': {
                    'name': {
                        'firstName': self.first_name,
                        'lastName': self.last_name,
                    },
                    'birthday': '2000-01-01',
                    'primaryAddress': {
                        'country': 'RUS',
                    },
                },
                'verificationInfo': {
                    'id': verification_id,
                    'answer': verification_email_answer,
                },
                'preferences': {
                    'preferredLanguage': 'ru_RU',
                    'marketingPreferences': {
                        'appleNews': False,
                        'appleUpdates': True,
                        'iTunesUpdates': True,
                    },
                },
            },
        }
        verification_phone_response = self.session.put('https://appleid.apple.com/account/verification/phone',
                                                       headers=headers, json=json_data)
        return verification_phone_response

    # 201
    def account(self, x_apple_hc, verification_phone_response, security_code, verification_id, verification_email_answer):
        headers = {
            'X-APPLE-HC': x_apple_hc,
            'scnt': verification_phone_response.headers.get('scnt')
        }
        json_data = {
            'phoneNumberVerification': {
                'phoneNumber': {
                    'id': 1,
                    'number': self.phone_number,
                    'countryCode': self.country_code_2,
                    'countryDialCode': '',
                    'nonFTEU': False,
                },
                'securityCode': {
                    'code': security_code,
                },
                'mode': 'sms',
            },
            'account': {
                'name': self.email,
                'password': self.password,
                'person': {
                    'name': {
                        'firstName': self.first_name,
                        'lastName': self.last_name,
                    },
                    'birthday': '2000-01-01',
                    'primaryAddress': {
                        'country': 'RUS',
                    },
                },
                'verificationInfo': {
                    'id': verification_id,
                    'answer': verification_email_answer,
                },
                'preferences': {
                    'preferredLanguage': 'ru_RU',
                    'marketingPreferences': {
                        'appleNews': False,
                        'appleUpdates': True,
                        'iTunesUpdates': True,
                    },
                },
            },
            'privacyPolicyChecked': False,
        }
        account_response = self.session.post('https://appleid.apple.com/account', headers=headers, json=json_data)
        return account_response
