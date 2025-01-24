import json
import hashlib
import socket
from datetime import datetime
import base64
import random

import socks

from loguru import logger
from DurakOnline import utils


class DurakSocketClient:
    def __init__(self, platform: str = 'ios'):
        self.sock = None
        self.data: dict = {}
        self.platform = platform
        self.original_socket = socket.socket

    @staticmethod
    def set_proxy(proxy_type, proxy_address, proxy_port, proxy_username=None, proxy_password=None):
        socks.set_default_proxy(proxy_type, proxy_address, proxy_port, username=proxy_username, password=proxy_password)
        socket.socket = socks.socksocket

    # Создание сокета с прокси
    def create_with_proxy(self, proxy_type, proxy_address, proxy_port, proxy_username=None, proxy_password=None):
        self.set_proxy(proxy_type, proxy_address, proxy_port, proxy_username, proxy_password)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Создание сокета без прокси
    def create_without_proxy(self):
        socket.socket = self.original_socket  # Восстанавливаем оригинальный сокет без прокси
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, server):
        server_address = (server['host'], server['port'])
        self.sock.connect(server_address)

    def get_server_sign_key(self):
        data = {
            "command": "c",
            "l": "ru",
            "tz": "+02:00",
            "t": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z",
            "pl": self.platform,
            "p": 10,
        }
        if self.platform == "ios":
            data.update({
                "v": "1.9.1.5",
                "ios": "14.4",
                "d": "iPhone8,4",
                "n": "durak.ios",
            })
        else:
            data.update({
                "v": "1.9.15",
                "d": "xiaomi cactus",
                "and": 28,
                "n": f"durak.{self.platform}",
            })
        self.sock.sendall(
            utils.marshal(
                data
            ).encode()
        )
        response_data = self.sock.recv(4096).decode()
        response_data2 = self.sock.recv(4096).decode()
        key = utils.un_marshal(response_data)
        key = key[0]["key"]
        return key

    def verify_session(self, server_sign_key, client_sign_key):
        verify_data = base64.b64encode(hashlib.md5((server_sign_key + client_sign_key).encode()).digest()).decode()
        self.sock.sendall(
            utils.marshal(
                {
                    "hash": verify_data,
                    "command": "sign"
                }
            ).encode()
        )
        response_data = self.sock.recv(4096).decode()
        response_data = utils.un_marshal(response_data)
        return response_data

    def google_auth(self, id_token):
        self.sock.sendall(
            utils.marshal(
                {
                    "id_token": id_token,
                    "command": "durak_google_auth"
                }
            ).encode()
        )
        response_data = self.sock.recv(4096).decode()
        response_data = utils.un_marshal(response_data)
        return response_data

    def apple_sign_in(self, id_token):
        self.sock.sendall(
            utils.marshal(
                {
                    "id_token": id_token,
                    "command": "apple_sign_in"
                }
            ).encode()
        )
        response_data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            response_data += temp_data
            temp_data = self.sock.recv(4096)
        response_data = response_data.decode('utf-8')
        response_data = utils.un_marshal(response_data)
        return response_data

    def auth(self, token):
        self.sock.sendall(
            utils.marshal(
                {
                    "token": token,
                    "command": "auth"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            data += temp_data
            temp_data = self.sock.recv(4096)
        data = data.decode('utf-8')

        if 'user_not_found' in data:
            return 'user_not_found'

        if data:
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
        return False

    def create_room(self, bet: int, password: str):
        self.sock.sendall(
            utils.marshal(
                {
                    "bet": bet,
                    "fast": False,
                    "sw": False,
                    "nb": True,
                    "ch": True,
                    "players": 2,
                    "deck": 36,
                    "password": password,
                    "command": "create"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        data += self.sock.recv(4096).decode()
        data += self.sock.recv(4096).decode()
        data += self.sock.recv(4096).decode()
        logger.debug(data)
        return utils.un_marshal(data)

    def get_validate_rw(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "get_validate_rw"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        data += self.sock.recv(4096).decode()
        logger.debug(data)
        return utils.un_marshal(data)

    def sendFriendRequest(self, user_id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": user_id,
                    "command": "friend_request"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            data += temp_data
            temp_data = self.sock.recv(4096)
        data = data.decode('utf-8')
        if 'user_not_found' in data:
            return 'user_not_found'
        if data:
            data = data.split('\n')
            other_keys = ['fl_update']
            response_json = {}
            for line in data:
                if not line:
                    continue
                if not any(line.startswith(key) for key in other_keys):
                    key = line.split('"k":')[1].replace('"', '').split(',v')[0]
                    try:
                        value = line.split('"v":')[1].replace('"', '').split('}')[0]
                    except IndexError:
                        value = None
                    response_json[key] = value
                for key in other_keys:
                    if line.startswith(key):
                        loads = json.loads(line.split(key, maxsplit=1)[1])
                        response_json[key] = loads
            return response_json
        return False

    def inviteToGame(self, user_id):
        self.sock.sendall(
            utils.marshal(
                {
                    "user_id": user_id,
                    "command": "invite_to_game"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)
        logger.debug(f"Invited to game")

    def ready(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "ready"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        return commands

    def surrender(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "surrender"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        logger.debug(f'Surrender {data}')
        return commands

    def exit(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "surrender"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)
        logger.debug(f"Game over")

    def getMessagesUpdate(self):
        data = self.sock.recv(1024).decode()
        messages = utils.un_marshal(data)
        logger.debug(messages)
        if 'user' in messages[1]:
            return messages[1].get("user")['id']
        return False

    def update_name(self, name: str):
        self.sock.sendall(
            utils.marshal(
                {
                    "value": name,
                    "command": "update_name"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        for command in commands:
            if not command:
                continue
            if command['k'] == 'name':
                self.data.update({
                    commands[0]['k']: commands[0]['v']
                })
        return commands

    def acceptFriendRequest(self, _id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id,
                    "command": "friend_accept"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        return commands

    def getInvites(self):
        data = utils.un_marshal(self.sock.recv(4096).decode())
        # logger.debug(data)
        if data[0].get("command") == "invite_to_game":
            gameId = data[0]["game_id"]
            return gameId
        return ""

    def join(self, room_id, password):
        self.sock.sendall(
            utils.marshal(
                {
                    "password": password,
                    "id": room_id,
                    "command": "join"
                },
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        return commands

    def leave(self, _id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id,
                    "command": "leave"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        return commands

    def deleteFriend(self, _id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id,
                    "command": "friend_delete"
                }
            ).encode()
        )
        for _ in range(3):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.debug(f"Friend has been deleted")

    def turn(self):
        card = random.choice(self.cards)
        self.sock.sendall(
            utils.marshal(
                {
                    "c": card,
                    "command": "t"
                }
            ).encode()
        )
        for _ in range(4):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.debug(f"[self._type.upper()] Played with card " + card)
        self.cards.remove(card)

    def waitingFor(self):
        while True:
            messages = utils.un_marshal(self.sock.recv(4096).decode())
            logger.debug(messages)
            for message in messages:
                if message.get("command") == "hand":
                    self.cards: list = message["cards"]
                elif message.get("command") == "turn":
                    self.trump = message["trump"]
                elif message.get("command") in ("mode", "end_turn", "t"):
                    return

    def take(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "take"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)

    def _pass(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "pass"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)

    def get_free_points(self):
        free_points = self.buy_points(0)
        return free_points

    def buy_points(self, _id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": f"com.rstgames.durak.points.{_id}",
                    "command": "buy_points"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        return commands

    def get_points_price(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "get_points_price"
                }
            ).encode()
        )
        data = b''
        temp_data = self.sock.recv(4096)
        while temp_data != b'\n':
            if temp_data.replace(b'\n', b'') == '':
                continue
            data += temp_data
            temp_data = self.sock.recv(4096)
        temp_data = self.sock.recv(4096)
        commands = utils.un_marshal(data.decode())
        return commands
