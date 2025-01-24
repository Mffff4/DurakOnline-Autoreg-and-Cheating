import random
from collections import OrderedDict

from durakonline import durakonline
from durakonline.utils import Server
from loguru import logger

ip = '65.21.92.166'
port = 10770

proxies = []
# Открываем файлы для чтения и записи
with open('../proxies.txt', 'r') as proxy_file:
    for _proxy in proxy_file.readlines():
        _proxy = _proxy.strip()
        if not _proxy:
            continue
        proxies.append(_proxy)


def process_token(token, proxy):
    for _try in range(3):
        try:
            bot_client = durakonline.Client(server_id=Server.EMERALD, proxy=proxy, ip=ip, port=port)
            bot_client.authorization.signin_by_access_token(token)
            return True
        except durakonline.objects.Err as err:
            if 'empty' in str(err):
                proxy = random.choice(proxies)
                continue
            return False
        except Exception as e:
            if 'recheck' in str(e):
                proxy = random.choice(proxies)
                continue
            logger.exception(e)
            return 'change_proxy'
    return False


def main():
    tokens = OrderedDict()  # Используем OrderedDict для уникальных значений и сохранения порядка
    with open('to_check_tokens.txt', 'r') as token_file:
        for token in token_file.readlines():
            token = token.strip()
            if not token:
                continue
            tokens[token] = None  # Добавляем токен как ключ
    tokens = list(tokens.keys())
    logger.info(f"Токенов найдено: {len(tokens)}")

    # Сохраняем без дубликатов
    with open('to_check_tokens.txt', 'w') as token_file:
        not_checked_tokens = "\n".join(tokens)
        token_file.write(not_checked_tokens)

    while tokens:
        token = tokens.pop(0)
        logger.info(f'Проверяю токен {token}')
        proxy = random.choice(proxies)
        result = process_token(token, proxy)

        if result == 'change_proxy':
            tokens.insert(0, token)
            logger.debug(f'Ошибка прокси, меняю')
            continue

        if not result:
            logger.info(f'Невалидный токен')
            # Сохраняем невалидные токены
            with open('invalid_tokens.txt', 'a') as invalid_file:
                invalid_file.write(f'{token}\n')
            continue

        # Сохраняем валидные токены
        with open('valid_tokens.txt', 'a') as valid_file:
            valid_file.write(f'{token}\n')
        logger.info(f'Валидный токен, сохранил')

        # Сохраняем остаток
        with open('to_check_tokens.txt', 'w') as token_file:
            not_checked_tokens = "\n".join(tokens)
            token_file.write(not_checked_tokens)

    logger.info('Проверил все токены')
    input("Press Enter to exit")


if __name__ == "__main__":
    main()
