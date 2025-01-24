import random
from collections import OrderedDict

try:
    import time

    from durakonline.utils import Server
    from loguru import logger

    import config
    from durakonline import durakonline, Game
except BaseException as e:
    print(f"Ошибка при импортировании модулей{e}")
    input("Press Enter to exit")


# c авторега: +100 -5000 (+...) / с бонуса: -1000 -250 -100 -100 (+1392)
def transfer_money_from_autoreg(main_client: durakonline.Client, bot_client: durakonline.Client):
    bets = [1000, 250, 100, 100]

    if main_client.info['points'] < max(bets) + 100 and bot_client.info['points'] < max(bets):
        return '[MAIN] Баланс менее 5100, у [BOT] менее 5000, перелив невозможен'
    elif main_client.info['points'] < max(bets) <= bot_client.info['points']:
        return '[MAIN] Баланс менее 5000 и [BOT] более 5000, перелив невозможен'
    elif bot_client.info['points'] + 100 < max(bets):
        return '[BOT] Баланс менее 4999, перелив невозможен'

    # if bot_client.info['points'] < max(bets) <= bot_client.info['points'] + 100:
    #     bets = [100] + bets

    for index, current_bet in enumerate(bets):
        logger.debug(f'Текущая ставка: {current_bet}')

        password = "1234"
        game: Game | None = None
        try:
            game = bot_client.game.create(bet=current_bet, password=password)
        except durakonline.objects.Err as err:
            logger.error(err)
            return 'невозможно'
        except Exception as e:
            logger.exception(e)
            if 'You cannot play two games under one user' in e.args:
                bot_client.game.surrender()
                create_room = bot_client.game.create(bet=current_bet, password=password)

        room_id = game.id

        join = main_client.game.join(password, room_id)

        bot_client.game.ready()
        main_client.game.ready()
        logger.info('Игра началась, жду 1 секунду')
        time.sleep(1)

        if index == 0 and len(bets) == 2:
            main_client.game.surrender()
            logger.info('[MAIN] Сдался, игра закончена')
        else:
            bot_client.game.surrender()
            logger.info('[BOT] Сдался, игра закончена')

        bot_client.game.leave(room_id)
        logger.info('[BOT] Вышел из команты')

        main_client.game.leave(room_id)
        logger.info('[MAIN] Вышел из комнаты, жду 1 секунду')
        time.sleep(1)

    return 'Закончил перелив с авторега, меняю'


def get_bonus(client: durakonline.Client):
    try:
        buy_points = client.buy_points(0)
        return buy_points
    except Exception as e:
        return False


def main():
    tokens = OrderedDict()  # Используем OrderedDict для уникальных значений и сохранения порядка
    with open('reged_tokens.txt', 'r') as token_file:
        for token in token_file.readlines():
            token = token.strip()
            if not token:
                continue
            tokens[token] = None  # Добавляем токен как ключ
    tokens = list(tokens.keys())
    logger.info(f"Токенов найдено: {len(tokens)}")

    if not tokens:
        logger.info('Не найдено токенов в файле reged_tokens.txt')

    main_client = durakonline.Client(server_id=Server.EMERALD)
    main_client.authorization.signin_by_access_token(config.MAIN_TOKEN)
    update_name = main_client.update_name('LvnLvn main drop')
    logger.info(f"[MAIN] {main_client.info['name']} | ID: {main_client.uid} | P: {main_client.info['points']}\n")

    ip = '65.21.92.166'
    port = 10770

    proxies = []
    # Открываем файлы для чтения и записи
    with open('proxies.txt', 'r') as proxy_file:
        for _proxy in proxy_file.readlines():
            _proxy = _proxy.strip()
            if not _proxy:
                continue
            proxies.append(_proxy)

    while tokens:
        token = tokens.pop(0)
        logger.info(f"Начинаю работать с {token}")
        for _try in range(3):
            try:
                proxy = random.choice(proxies)
                bot_client = durakonline.Client(server_id=Server.EMERALD, proxy=proxy, ip=ip, port=port)
                # bot_client = durakonline.Client(server_id=Server.EMERALD, ip=ip, port=port)
                bot_client.authorization.signin_by_access_token(token)

                update_name = bot_client.update_name('LvnLvn zelenka.guru')

                # bot_client = durakonline.Client(server_id=Server.EMERALD, proxy=proxy)
                # bot_client.authorization.signin_by_access_token(token)

                logger.info(f"[MAIN] {main_client.info['name']} | ID: {main_client.uid} | P: {main_client.info['points']}")
                logger.info(f"[BOT] {bot_client.info['name']} | ID: {bot_client.uid} | P: {bot_client.info['points']}")

                bonus = get_bonus(bot_client)
                # logger.info(bonus)
                if bonus:
                    logger.info(f"[BOT] Получил бонус")
                    logger.info(f"[BOT] {bot_client.info['name']} | ID: {bot_client.uid} | P: {bot_client.info['points']}")

                    result = transfer_money_from_autoreg(main_client, bot_client)
                    logger.info(result)
                    if 'невозможен' not in result:
                        logger.info(
                            f"[BOT] {bot_client.info['name']} | ID: {bot_client.uid} | P: {bot_client.info['points']}")

                else:
                    logger.info(f"[BOT] Бонус уже получен")

                break
            except durakonline.objects.Err as err:
                if 'empty' in str(err):
                    continue
                logger.info("Невалидный токен")
                break
            except Exception as e:
                if 'recheck' in str(e):
                    continue
                logger.exception(e)
                continue

        logger.info('---------------------------------------------------------')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(e)
    finally:
        input('Press Enter to exit')
