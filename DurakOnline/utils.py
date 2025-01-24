import json
from enum import Enum

import requests
import socks
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector


class ProxyType(Enum):
    HTTP = socks.HTTP
    SOCKS4 = socks.SOCKS4
    SOCKS5 = socks.SOCKS5

    @classmethod
    def from_string(cls, proxy_type_str):
        # Преобразуем строковое значение в значение прокси socks, игнорируя регистр
        proxy_type_str = proxy_type_str.lower()
        if proxy_type_str == 'http' or proxy_type_str == 'https':
            return cls.HTTP.value  # Вернем socks.HTTP
        elif proxy_type_str == 'socks4':
            return cls.SOCKS4.value  # Вернем socks.SOCKS4
        elif proxy_type_str == 'socks5':
            return cls.SOCKS5.value  # Вернем socks.SOCKS5
        else:
            raise ValueError(f"Некорректный тип прокси: {proxy_type_str}")


def to_bytes(data):
    return data.encode()


def marshal(data, other=''):
    command = data.pop('command')
    return other + command + json.dumps(data, separators=(',', ':')).replace("{}", '')


def un_marshal(data):
    result = [{}]
    for i in data.strip().split('\n'):
        pos = i.find('{')
        command = i[:pos]
        try:
            message = json.loads(i[pos:])
        except Exception:
            message = {}
            continue
        message['command'] = command
        result.append(message)

    return result[1:] if len(result) > 1 else result


def who_first(main_cards, bot_cards, trump):
    trump_m = trump[0]
    _minC = 14
    whos = ""
    for main_card in main_cards:
        main_card = main_card.replace('J', '11').replace('Q', '12').replace('K', '13').replace('A', '14')
        for bot_card in bot_cards:
            bot_card = bot_card.replace('J', '11').replace('Q', '12').replace('K', '13').replace('A', '14')
            if main_card[0] == trump_m and bot_card[0] == trump_m:
                if _minC > min(int(bot_card[1:]), int(main_card[1:])):
                    _minC = min(int(bot_card[1:]), int(main_card[1:]))
                    whos = "bot" if int(bot_card[1:]) < int(main_card[1:]) else "main"
    if whos == "":
        if trump_m in "".join(bot_cards):
            whos = "bot"
        else:
            whos = "main"
    return whos


async def get_servers_async(timeout: int = 15, connector: ProxyConnector = None) -> dict:
    headers = {
        'User-Agent': 'FoolAndoid/1.9.15 Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I003DD Build/PI)'
    }
    async with ClientSession(timeout=ClientTimeout(total=timeout), connector=connector) as session:
        response = await session.get(url='http://static.rstgames.com/durak/servers.json', headers=headers)
        json_data: dict = await response.json(content_type=response.content_type)
        servers = json_data['user']
        return servers


def get_servers(timeout: int = 15, proxies: dict = None) -> dict:
    headers = {
        'User-Agent': 'FoolAndoid/1.9.15 Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I003DD Build/PI)'
    }
    response = requests.get(url='http://static.rstgames.com/durak/servers.json', headers=headers,
                            proxies=proxies, timeout=timeout)
    json_data: dict = response.json()
    servers = json_data['user']
    return servers
