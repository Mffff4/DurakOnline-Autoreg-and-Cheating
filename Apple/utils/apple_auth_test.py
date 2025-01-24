import asyncio
import hashlib
import base64
import os
from Crypto.Hash import keccak


# Группы для криптографических операций
class Groups:
    group_2048 = {
        "N": "AC6BDB41 324A9A9B F166DE5E 1389582F AF72B665 1987EE07 FC319294 3DB56050 A37329CB B4A099ED 8193E075 7767A13D D52312AB 4B03310D CD7F48A9 DA04FD50 E8083969 EDB767B0 CF609517 9A163AB3 661A05FB D5FAAAE8 2918A996 2F0B93B8 55F97993 EC975EEA A80D740A DBF4FF74 7359D041 D5C33EA7 1D281E44 6B14773B CA97B43A 23FB8016 76BD207A 436C6481 F1D2B907 8717461A 5B9D32E6 88F87748 544523B5 24B0D57D 5EA77A27 75D2ECFA 032CFBDB F52FB378 61602790 04E57AE6 AF874E73 03CE5329 9CCC041C 7BC308D8 2A5698F3 A8D0C382 71AE35F8 E9DBFBB6 94B5C803 D89F7AE4 35DE236D 525F5475 9B65E372 FCD68EF2 0FA7111F 9E4AFF73",
        "g": "02"
    }

# Преобразование строки в байты
def string_to_bytes(string):
    return string.encode('utf-8')

# Сложение двух чисел
def add_numbers(a, b):
    return a + b

# Умножение двух чисел
def multiply_numbers(a, b):
    return a * b

# Модульное деление с обработкой отрицательных значений
def modulo(a, b):
    result = a % b
    if result < 0:
        result = add_numbers(result, b)
    return result

# Быстрое возведение в степень по модулю
def modular_exponentiation(base, exponent, modulus):
    if modulus == 1:
        return 0
    result = 1
    base %= modulus
    while exponent > 0:
        if exponent % 2 == 1:
            result = (result * base) % modulus
        exponent >>= 1
        base = (base * base) % modulus
    return result

# Класс для управления объектами: чисел, буферов, хешей и других данных
class ObjectManager:
    def __init__(self, value):
        self._bigint = None
        self._buffer = None
        self._hex = None
        self._hash = None
        self._base64 = None

        # Определение типа данных при инициализации
        if isinstance(value, str):
            self._hex = value
        elif isinstance(value, (bytearray, bytes)):
            self._buffer = bytearray(value)
        elif isinstance(value, int):
            self._bigint = value
        else:
            raise TypeError("Unsupported type for ObjectManager")

    # Преобразование в большое целое число
    def bigint(self):
        if self._bigint is None:
            self._bigint = int(self.hex(), 16)
        return self._bigint

    # Преобразование в байтовый буфер
    def buffer(self):
        if self._buffer is None:
            self._buffer = self.hex_to_buffer(self.hex())
        return self._buffer

    # Преобразование в шестнадцатеричное представление
    def hex(self):
        if self._hex is None:
            if self._bigint is not None:
                self._hex = hex(self._bigint)[2:]
            else:
                self._hex = ''.join(f'{byte:02x}' for byte in self._buffer)
        return self._hex

    # Получение хеша
    def get_hash(self):
        if self._hash is None:
            # sha256_hash = hashlib.sha256(self.buffer()).hexdigest()

            sha256_hash = keccak.new(data=self.buffer(), digest_bits=512).digest()
            sha256_hash = sha256_hash.hex()

            self._hash = ObjectManager(sha256_hash)
        return self._hash

    # Дополнение до длины другого буфера
    def pad(self, other):
        return ObjectManager(bytearray(other.buffer()) + bytearray(self.buffer()))

    # Преобразование в base64
    def get_base64(self):
        if self._base64 is None:
            self._base64 = base64.b64encode(self.buffer()).decode('utf-8')
        return self._base64

    # Преобразование из шестнадцатеричной строки в байтовый буфер
    @staticmethod
    def hex_to_buffer(hex_string):
        if len(hex_string) % 2 == 1:
            hex_string = "0" + hex_string
        return bytearray.fromhex(hex_string)

    # Конкатенация нескольких буферов
    @staticmethod
    def concat(*objects):
        combined_buffer = bytearray()
        for obj in objects:
            combined_buffer += obj.buffer()
        return ObjectManager(combined_buffer)

# Генерация случайных байтов
def get_random_bits():
    return ObjectManager(os.urandom(32))

# Преобразование строки base64 в массив байтов
def base64_to_bytes(base64_string):
    return bytearray(base64.b64decode(base64_string))

# Инициализация группы
def init_group(group_size):
    if group_size != 2048:
        raise ValueError(f"Group {group_size} not supported.")
    group = Groups.group_2048
    group_hex = group["N"].replace(" ", "")
    group_generator = group["g"]

    return {
        "N": ObjectManager(group_hex),
        "g": ObjectManager(group_generator)
    }

# Пример класса для управления учетной записью
class AccountManager:
    def __init__(self, account_name):
        self._private_value = None
        self._public_value = None
        self.account_name = account_name

    # Получение приватного значения
    def private_value(self):
        if self._private_value is None:
            self._private_value = get_random_bits()
        return self._private_value

    # Получение публичного значения
    def public_value(self):
        if self._public_value is None:
            group = init_group(2048)
            N = group["N"]
            g = group["g"]
            self._public_value = N.pad(ObjectManager(modular_exponentiation(g.bigint(), self.private_value().bigint(), N.bigint())))
        return self._public_value

    # Генерация сообщения подтверждения
    async def generate_evidence_message(self, params):
        iterations = params["iterations"]
        server_public_value = params["serverPublicValue"]
        salt = params["salt"]
        password = params["password"]
        protocol = params.get("protocol", "s2k")

        private_value = self.private_value()
        public_value = self.public_value()
        server_obj = ObjectManager(server_public_value)
        salt_obj = ObjectManager(salt)
        account_name_obj = ObjectManager(string_to_bytes(self.account_name.lower()))

        # Здесь выполняется логика обработки данных для подтверждения
        # Пример: создание хешей, конкатенация буферов и т.д.

        # Пример генерации финальных данных для подтверждения
        final_result = {
            "M1": public_value.get_base64(),
            "M2": server_obj.get_base64()
        }
        return final_result


async def get_complete_data(s):
    iterations = s['iterations']
    server_public_value = base64.b64decode(s['b'])
    salt = base64.b64decode(s['salt'])
    password = s['password']
    protocol = s.get('protocol', 's2k')  # Протокол по умолчанию 's2k'

    # Получение данных подтверждения с использованием AccountManager
    data = await AccountManager('email@gmail.com').generate_evidence_message({
        'iterations': iterations,
        'serverPublicValue': server_public_value,
        'salt': salt,
        'password': password,
        'protocol': protocol
    })
    print(data)
    return data

if __name__ == "__main__":
    s = {
        'password': 'Qq!1qwerr',
          "iterations": 20534,
          "salt": "D5ciiiTlXwQj8x+8foSvtg==",
          "protocol": "s2k",
          "b": "LMkcjUAgLd4t5rSJRV7QWWj4T/h35yiidt3xEOLPgp5EjTptRxL9Fenj1mxPv1VlRhlz8W9cwxu4HdCBkQCGayOwdA3ZT4IJg/7SEY4YLWyVPLgAXYSlSwm+SgpS3bQGW49XkOWiOo/SPQoiS4DdtExeqHVhbhJ+s36FbJDn5uHGpcrlMHvmGjLUvE3N73ursSjlFcLGatm61CJaOaLOpZd9+GJaoQL3hx13YubInGhjpwlYyysdxs+WPvKdE3hAvkHuuo0dZjlwV9vcyw3FKHdlpdE6Y7gSyxYgyxofkEhhal/Ca5QsP6tncyVOYT3y1/Z+1RCqBQ2hBYeIn9UibA==",
          "c": "d-13a-685bc190-7e4d-11ef-91cf-833aafded2cd:RNO"
        }
    asyncio.run(get_complete_data(s))
