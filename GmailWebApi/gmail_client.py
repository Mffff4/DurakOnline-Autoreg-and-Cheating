import os

import requests
from GmailWebApi.models import Cookie, Session

HEADERS = {
    "Referer": "https://ogs.google.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
}


class GmailClient:
    def __init__(self, cookies_file: str):
        self.session = requests.session()
        self.sessions = []

        cookies = self.__get_cookies_from_file(cookies_file)

        self.session.headers.update(HEADERS)
        for cookie in cookies:
            self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)

    @staticmethod
    def __get_cookies_from_file(file_path: str) -> list[Cookie]:
        if not os.path.exists(file_path):
            return []

        parsed_cookies = []
        with open(file_path, "r", errors="ignore", encoding="utf-8") as cookies_file:
            file_content = cookies_file.read().splitlines()

        for cookie_line in file_content:
            if "google." not in cookie_line:
                continue

            try:
                cookie_line = cookie_line.split('\t')
                domain = cookie_line[0]
                cookie_name = cookie_line[5]
                cookie_value = cookie_line[6]
                cookie_item = Cookie(cookie_name, cookie_value, domain)
                parsed_cookies.append(cookie_item)
            except IndexError:
                continue

        return parsed_cookies

    def get_sessions(self) -> list[Session]:
        params = {
            "listPages": "0",
            "pid": "23",
            "gpsia": "1",
            "source": "ogb",
            "atic": "1",
            "mo": "1",
            "mn": "1",
            "hl": "fr",
            "ts": "72"
        }

        response = self.session.post(
            url="https://accounts.google.com/ListAccounts",
            params=params
        ).json()

        for session in response[1]:
            is_alive = session[9]
            if not is_alive:
                continue

            self.sessions.append(Session(
                name=session[2],
                email=session[3],
                avatar=session[4],
                index=session[7],
                account_id=session[10]
            ))

        return self.sessions



