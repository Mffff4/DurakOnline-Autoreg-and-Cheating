import base64
import hashlib
import json
import os
import socket
from datetime import datetime

import socks
import websocket
from loguru import logger

from DurakOnline import utils


class DurakWebSocketClient:
    def __init__(self):
        self.sock: websocket.WebSocket | None = None
        self.data: dict = {}
        self.headers: dict = {
            "Upgrade": "websocket",
            "Origin": "https://durak.rstgames.com",
            "Cache-Control": "no-cache",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Pragma": "no-cache",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": base64.b64encode(os.urandom(16)).decode('utf-8'),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        }
        self.original_socket = socket.socket

    def create_with_proxy(self, proxy_type, proxy_address, proxy_port, proxy_username=None, proxy_password=None):
        # Устанавливаем прокси для библиотеки socket через socks
        socks.set_default_proxy(proxy_type, proxy_address, proxy_port, username=proxy_username, password=proxy_password)
        socket.socket = socks.socksocket

        # Создаем WebSocket объект
        self.sock = websocket.WebSocket()

    def create_without_proxy(self):
        # Восстанавливаем оригинальный сокет без прокси
        socket.socket = self.original_socket

        # Создаем WebSocket объект
        self.sock = websocket.WebSocket()

    def connect(self, server):
        server_address = server['web_url']
        self.sock.connect(server_address)

    def get_server_sign_key(self):
        data = {
            "command": "c",
            "l": "ru",
            "tz": "+02:00",
            "t": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "pl": 'ios',
            "p": 10,
            "v": "1.9.1.5",
            "ios": "14.4",
            "d": "iPhone8,4",
            "n": "durak.ios",
        }
        self.sock.send(
            utils.marshal(
                data
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        key = commands[0]["key"]
        return key

    def verify_session(self, server_sign_key, client_sign_key):
        verify_data = base64.b64encode(hashlib.md5((server_sign_key + client_sign_key).encode()).digest()).decode()
        self.sock.send(
            utils.marshal(
                {
                    "hash": verify_data,
                    "command": "sign"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def apple_sign_in(self, id_token):
        self.sock.send(
            utils.marshal(
                {
                    "id_token": id_token,
                    "command": "apple_sign_in"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def auth(self, token):
        self.sock.send(
            utils.marshal(
                {
                    "token": token,
                    "command": "auth"
                }
            ).encode()
        )
        data = self.read_last_messages()

        if 'user_not_found' in data:
            return 'user_not_found'

        if data:
            data = self.parse_profile(data)
            return data

        return False

    def parse_profile(self, data):
        data = data.split('\n')
        other_keys = ['authorized', 'free', 'server', 'tour', 'ad_nets']
        for line in data:
            if not line or 'confirmed' in line:
                continue
            if not any(line.startswith(key) for key in other_keys):
                key = line.split('"k":')[1].replace('"', '').split(',v')[0]
                try:
                    value = line.split('"v":')[1].replace('"', '').split('}')[0]
                except IndexError:
                    value = None
                self.data[key] = value
            for key in other_keys:
                if line.startswith(key):
                    loads = json.loads(line.split(key, maxsplit=1)[1])
                    self.data[key] = loads
        return self.data

    def create_room(self, bet: int = 100, fast: bool = False, sw: bool = False, nb: bool = True, ch: bool = True,
                    players: int = 2, deck: int = 36, password: str = ''):
        self.sock.send(
            utils.marshal(
                {
                    "bet": bet,
                    "fast": fast,
                    "sw": sw,
                    "nb": nb,
                    "ch": ch,
                    "players": players,
                    "deck": deck,
                    "password": password,
                    "command": "create"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return data

    def ready(self):
        self.sock.send(
            utils.marshal(
                {
                    "command": "ready"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def surrender(self):
        self.sock.send(
            utils.marshal(
                {
                    "command": "surrender"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def update_name(self, name: str):
        self.sock.send(
            utils.marshal(
                {
                    "value": name,
                    "command": "update_name"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        for command in commands:
            if not command:
                continue
            if command['k'] == 'name':
                self.data.update({
                    commands[0]['k']: commands[0]['v']
                })
        return commands

    def accept_friend_request(self, _id):
        self.sock.send(
            utils.marshal(
                {
                    "id": _id,
                    "command": "friend_accept"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def join(self, room_id, password):
        self.sock.send(
            utils.marshal(
                {
                    "password": password,
                    "id": room_id,
                    "command": "join"
                },
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def leave(self, _id):
        self.sock.send(
            utils.marshal(
                {
                    "id": _id,
                    "command": "leave"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def get_free_points(self, _id):
        self.sock.send(
            utils.marshal(
                {
                    "id": _id,
                    "command": "buy_points"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def buy_points(self, _id):
        self.sock.send(
            utils.marshal(
                {
                    "id": f"com.rstgames.durak.points.{_id}",
                    "command": "buy_points"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def get_points_price(self):
        self.sock.send(
            utils.marshal(
                {
                    "command": "get_points_price"
                }
            ).encode()
        )
        data = self.read_last_messages()
        commands = utils.un_marshal(data)
        return commands

    def read_last_messages(self):
        data = ''
        while (temp_data := self.sock.recv()) != '\n':
            data += temp_data + '\n'
        logger.debug(data)
        return data
