from requests import Session, Response

from SMSHubOrg.properties import SetStatus


class SMSHubApi:
    def __init__(self, api_key: str, proxy: dict):
        self.api_key = api_key
        self.session = Session()
        self.session.proxies = proxy

    def get_numbers_status(self, country, operator='') -> Response:
        params = {
            'api_key': self.api_key,
            'action': 'getNumbersStatus',
            'country': country,
            'operator': operator
        }
        response = self.session.get(url=f'https://smshub.org/stubs/handler_api.php', params=params)
        return response

    def get_balance(self) -> Response:
        params = {
            'api_key': self.api_key,
            'action': 'getBalance'
        }
        response = self.session.get(url=f'https://smshub.org/stubs/handler_api.php', params=params)
        return response

    def get_number(self, service, operator, country, max_price) -> Response:
        params = {
            'api_key': self.api_key,
            'action': 'getNumber',
            'service': service,
            'operator': operator,
            'country': country,
            'maxPrice': max_price
        }
        response = self.session.get(url=f'https://smshub.org/stubs/handler_api.php', params=params)
        return response

    def set_status(self, status: SetStatus, acivation_id) -> Response:
        params = {
            'api_key': self.api_key,
            'action': 'setStatus',
            'status': status.value,
            'id': acivation_id
        }
        response = self.session.get(url=f'https://smshub.org/stubs/handler_api.php', params=params)
        return response

    def get_status(self, acivation_id) -> Response:
        params = {
            'api_key': self.api_key,
            'action': 'getStatus',
            'id': acivation_id
        }
        response = self.session.get(url=f'https://smshub.org/stubs/handler_api.php', params=params)
        return response

    def get_prices(self, service, country) -> Response:
        params = {
            'api_key': self.api_key,
            'action': 'getPrices',
            'service': service,
            'country': country
        }
        response = self.session.get(url=f'https://smshub.org/stubs/handler_api.php', params=params)
        return response
