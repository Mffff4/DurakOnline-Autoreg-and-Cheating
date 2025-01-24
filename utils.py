from base64 import b64decode, b64encode

from durakonline import durakonline
from durakonline.utils import Server
from loguru import logger
from requests import Session


def solve_captcha_with_xevil(captcha_content, session: Session):
    captcha_answer = None
    try:
        data = {
            "task": {
                "type": "ImageToTextTask",
                "body": captcha_content,
            },
        }
        response = session.post(
            'http://localhost:80/createTask',
            json=data,
        )
        response_json = response.json()

        data = {
            "clientKey": "clientKey",
            "taskId": response_json['taskId']
        }
        response = session.post(f'http://localhost:80/getTaskResult', json=data)
        captcha_answer = response.json()
        captcha_answer = captcha_answer['solution']['text']
        return captcha_answer
    except Exception as e:
        logger.info(f"Ошибка соединения с XEvil: {e} | captcha_answer: {captcha_answer}")
        return None


def get_enctypted_a(email, session: Session):
    try:
        data = {
            "email": email
        }
        response_get_encrypted_a = session.post('http://localhost:3000/get_encrypted_a', json=data)
        encrypted_a = response_get_encrypted_a.json()
        return encrypted_a
    except Exception as e:
        logger.info(f'Не запущен JS сервер: {e}')
        return {}


def get_complete_data(data: dict, session: Session):
    try:
        complete_data_response = session.post('http://localhost:3000/get_complete_data', json=data)
        complete_data_json = complete_data_response.json()
        return complete_data_json
    except Exception as e:
        logger.info(f'Не запущен JS сервер: {e}')
        return {}


def get_tokens_by_apple_id_token(apple_id_token: str):
    client = durakonline.Client(server_id=Server.EMERALD)
    commands = client.authorization.apple_sign_in(apple_id_token)

    tokens = []
    for token in list(commands['users'].keys()):
        tokens.append(token)
    return tokens
