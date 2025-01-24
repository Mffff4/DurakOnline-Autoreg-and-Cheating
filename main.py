import logging
import os
import random
from datetime import datetime
from time import sleep

from requests import Session
from loguru import logger

import config
from Apple.auth_durak_webapi import AuthDurakWebApi
from Apple.utils.utils import solve_apple_challenge
from GmailWebApi import models
from SMSHubOrg.api import SMSHubApi
from SMSHubOrg.properties import SetStatus
from Apple.web_api import WebAPI
from GmailWebApi.gmail_client import GmailClient
from utils import solve_captcha_with_xevil, get_enctypted_a, get_complete_data, get_tokens_by_apple_id_token

logging.getLogger('asyncio').setLevel(logging.CRITICAL)


def get_txt_files(directory, shuffle=False):
    txt_files = []
    for file in os.listdir(directory):
        if file.endswith(".txt"):
            txt_files.append(os.path.join(directory, file))
    return random.shuffle(txt_files) if shuffle else txt_files


def get_number(smshub: SMSHubApi):
    get_prices_response = smshub.get_prices(service='wx', country='0')
    get_prices_json = get_prices_response.json()

    if not get_prices_json['0']['wx']:
        logger.debug('По заданным параметрам номеров не найдено')
        return False

    min_price = list(map(float, get_prices_json['0']['wx'].keys()))[config.NUM_OF_NUMBERS]

    if min_price > config.MAX_PRICE:
        logger.debug(f'Минимальная цена для номера {min_price}, она выше MAX_PRICE. Измените MAX_PRICE в config.py')
        return False

    get_number_response = smshub.get_number(service='wx', operator='any', country='0', max_price=min_price)
    get_number_text = get_number_response.text

    get_number_status = get_number_text.split(':')[0]
    if get_number_status == 'NO_NUMBERS':
        logger.debug('Нет номеров с заданными параметрами')
        return False

    if get_number_status != 'ACCESS_NUMBER':
        logger.debug(f'Невалидный get_number_status: {get_number_status}')
        return False

    activation_id = get_number_text.split(':')[1]
    account_number = get_number_text.split(':')[2]
    return activation_id, account_number


FIRST_AUTH = config.FIRST_AUTH


def main():
    local_session = Session()

    smshub = SMSHubApi(api_key=config.SMSHUB_APIKEY, proxy={'http': f'{config.SMSHUB_PROXY_TYPE}://{config.SMSHUB_PROXY}', 'https': f'{config.SMSHUB_PROXY_TYPE}://{config.SMSHUB_PROXY}'})

    activation_id = None
    account_number = None

    account_email = None

    logger.info('Начинаю делать магию...')

    all_cookies_files = get_txt_files(r'C:\Users\Admin\Desktop\Gmail Cookies', shuffle=False)
    for cookies_file in all_cookies_files:
        if config.EMAIL_USE_ONLY_GMAIL_DOMAINS and '@gmail.com' not in cookies_file:
            continue

        gmail_client: GmailClient | None = None
        current_session: models.Session | None = None
        if config.EMAIL_USE_MY:
            account_email = config.EMAIL_USE_MY
        elif config.EMAIL_SELF_ENTER_EMAIL:
            account_email = input('Введите email: ')
        else:
            gmail_client = GmailClient(cookies_file=str(cookies_file))
            sessions = gmail_client.get_sessions()
            for session in sessions:
                if session.email in cookies_file:
                    current_session = session
                    account_email = current_session.email
                    break
            else:
                logger.debug('Сессия умерла, пропускаю')
                continue

        logger.info(f'Начинаю работать с {account_email}')

        apple_webapi: WebAPI | None = None
        while True:
            if FIRST_AUTH:
                if not account_number and not activation_id:
                    get_number_result = get_number(smshub)
                    if get_number_result:
                        activation_id, account_number = get_number_result
                    else:
                        continue

                apple_webapi = WebAPI(account_email, config.APPLE_ACCOUNT_PASSWORD, account_number, config.APPLE_ACCOUNT_FIRST_NAME, config.APPLE_ACCOUNT_LAST_NAME, config.COUNTRY_CODE_1, config.COUNTRY_CODE_2, config.APPLE_FINGERPRINT)
                if config.APPLE_USE_PROXY:
                    apple_webapi.session.proxies = {
                       'http': f'{config.APPLE_PROXY_TYPE}://{config.APPLE_PROXY}',
                       'https': f'{config.APPLE_PROXY_TYPE}://{config.APPLE_PROXY}'
                    }

                # Register APPLE ID
                apple_webapi.update_client_id()
                apple_webapi.update_widget_key()

                widget_account_response = apple_webapi.widget_account()
                stamp = f"1:{widget_account_response.headers.get('X-Apple-HC-Bits')}:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}:{widget_account_response.headers.get('X-Apple-Hc-Challenge')}"
                x_apple_hc = solve_apple_challenge(stamp)

                captcha_answer = ''
                captcha_response = None
                captcha_id = None
                captcha_token = None
                while not captcha_answer or '*' in captcha_answer or 'xevil' in captcha_answer.lower():
                    captcha_response = apple_webapi.captcha(widget_account_response=widget_account_response)
                    if captcha_response.status_code != 201:
                        logger.debug('Captcha response invalid')
                        continue
                    captcha = captcha_response.json()
                    captcha_content = captcha['payload']['content']
                    captcha_id = captcha['id']
                    captcha_token = captcha['token']
                    widget_account_response = captcha_response
                    captcha_answer = ''
                    captcha_answer = solve_captcha_with_xevil(captcha_content, local_session)
                    logger.debug(f'Captcha answer: {captcha_answer}')

                # -34607001
                account_validate_response = apple_webapi.account_validate(x_apple_hc, captcha_response, captcha_id, captcha_token, captcha_answer)

                if '503 Service Temporarily Unavailable' in account_validate_response.text:
                    logger.debug('503 Service Temporarily Unavailable')
                    continue

                if 'Введите действительный адрес электронной почты, который будет использоваться как основной' in account_validate_response.text:
                    logger.debug('Этот адрес почты нельзя использовать')
                    break

                if 'Адрес электронной почты используется' in account_validate_response.text:
                    logger.debug('Адрес электронной почты используется другим')
                    break

                if 'Этот номер телефона нельзя использовать в данный момент' in account_validate_response.text or 'This phone number cannot be used at this time' in account_validate_response.text:
                    logger.debug('Этот номер телефона нельзя использовать в данный момент')
                    response_cancel = smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                    account_number = activation_id = None
                    continue

                if 'На этот номер отправлено слишком много кодов проверки' in account_validate_response.text:
                    logger.debug('На этот номер отправлено слишком много кодов проверки')
                    response_cancel = smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                    account_number = activation_id = None
                    continue

                if 'Неверный номер телефона' in account_validate_response.text:
                    logger.debug('Неверный номер телефона. Проверьте COUNTRY_CODE в Конфиге')
                    smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                    account_number = activation_id = None
                    continue

                if 'Для продолжения введите символы, которые Вы видите или слышите' in account_validate_response.text:
                    logger.debug('Для продолжения введите символы, которые Вы видите или слышите')
                    continue

                if 'В настоящее время невозможно создать учетную запись' in account_validate_response.text:
                    logger.debug(account_validate_response.text)
                    logger.debug("Проблема в Домене почте, IP не связанном с номером, Fingerprint, Номером телефона или чем-то другим")
                    get_status_response = smshub.get_status(activation_id)
                    status_text = get_status_response.text
                    while status_text != 'ACCESS_CANCEL' and 'STATUS_WAIT_RETRY' not in status_text and 'BAD_STATUS' not in status_text:
                        set_status_response = smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                        status_text = set_status_response.text
                    account_number = activation_id = None
                    break

                account_verification_post_response = apple_webapi.account_verification_post(account_validate_response)
                if 'Адрес электронной почты используется другим' in account_verification_post_response.text:
                    logger.debug('Адрес электронной почты используется другим')
                    break

                if 'Новый код невозможно отправить в настоящий момент' in account_verification_post_response.text:
                    logger.debug('Новый код невозможно отправить в настоящий момент')
                    break
                else:
                    try:
                        if 'Для продолжения введите символы, которые Вы видите или слышите' in account_verification_post_response.text:
                            logger.debug('Для продолжения введите символы, которые Вы видите или слышите')
                            continue
                        account_verification_post_json = account_verification_post_response.json()
                        verification_id = account_verification_post_json['verificationId']
                    except Exception as ex:
                        logger.error(ex)
                        logger.debug(f'Ошибка с ключом verificationId: {ex}')
                        continue

                email_code = ''
                current_time = datetime.now()
                while not email_code.isdigit():
                    if config.EMAIL_SELF_ENTER_CODE or config.EMAIL_USE_MY:
                        email_code = input('Введите код с почты: ')
                        break
                    elapsed_minutes = (datetime.now() - current_time).total_seconds() / 60
                    if elapsed_minutes > config.EMAIL_MINUTES_FOR_WAITING_CODE:
                        break
                    sleep(5)
                    email_code_response = gmail_client.session.get(f'https://mail.google.com/mail/u/{current_session.index}/')
                    email_code = email_code_response.text.split('\"\\\\u003e\\\\r\\\\n\\\\t\\\\t\\\\t\\\\t\\\\t\\\\t\\\\u003cp\\\\u003e\\\\u003cb\\\\u003e')[-1].split('\\')[0]

                if not email_code.isdigit():
                    logger.debug('Не удалось получить код c почты')
                    break

                verification_email_answer = email_code

                account_verification_put_response = apple_webapi.account_verification_put(account_verification_post_response, verification_id, verification_email_answer)
                if account_verification_put_response.status_code != 204:
                    logger.debug(account_verification_put_response.text)
                    if 'Неверный код проверки.' in account_verification_put_response.text:
                        continue
                    break

                stamp = f"1:{account_validate_response.headers.get('X-Apple-HC-Bits')}:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}:{account_validate_response.headers.get('X-Apple-Hc-Challenge')}"
                x_apple_hc = solve_apple_challenge(stamp)

                verification_phone_post_response = apple_webapi.verification_phone_post(x_apple_hc, account_verification_put_response, verification_id, verification_email_answer)
                if verification_phone_post_response.status_code != 201:
                    logger.debug(verification_phone_post_response.text)
                    break

                # Getting SMS
                current_time = datetime.now()
                code = None
                while not code:
                    if config.SMSHUB_SELF_ENTER_CODE:
                        code = input('Введите код из СМС: ')
                        break

                    elapsed_minutes = (datetime.now() - current_time).total_seconds() / 60
                    if elapsed_minutes > config.SMSHUB_MINUTES_FOR_WAITING_SMS_CODE:
                        break

                    get_status_response = smshub.get_status(activation_id)
                    get_status_text = get_status_response.text
                    if get_status_text.split(':')[0] != 'STATUS_OK':
                        sleep(1)
                    else:
                        code = get_status_text.split(':')[1]

                if not code:
                    smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                    account_number = activation_id = None
                    continue
                # Getting SMS

                verification_phone_put_response = apple_webapi.verification_phone_put(verification_phone_post_response,
                                                                                      code, verification_id,
                                                                                      verification_email_answer)
                if verification_phone_put_response.status_code != 201:
                    logger.debug(verification_phone_put_response.text)
                    smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                    account_number = activation_id = None
                    continue

                stamp = f"1:{verification_phone_post_response.headers.get('X-Apple-HC-Bits')}:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}:{verification_phone_post_response.headers.get('X-Apple-Hc-Challenge')}"
                x_apple_hc = solve_apple_challenge(stamp)

                account_response = apple_webapi.account(x_apple_hc, verification_phone_put_response, code,
                                                        verification_id, verification_email_answer)
                if account_response.status_code != 201:
                    logger.debug(account_response.text)
                    smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                    account_number = activation_id = None
                    break

                logger.info('Зарегистрировал...')
                # Register APPLE ID

            # Authorize APPLE ID to DURAK ONLINE:
            auth_durak_webapi = AuthDurakWebApi(account_email, config.APPLE_ACCOUNT_PASSWORD, config.APPLE_FINGERPRINT)
            auth_authorize_response = auth_durak_webapi.auth_authorize()

            auth_durak_webapi.update_x_apple_widget_key(auth_authorize_response)
            auth_durak_webapi.update_x_apple_auth_attributes(auth_authorize_response)

            auth_federate_response = auth_durak_webapi.auth_federate()
            if auth_federate_response.status_code != 200:
                logger.debug(auth_federate_response.text)
                continue

            encrypted_a: dict = {}
            while not encrypted_a:
                encrypted_a = get_enctypted_a(account_email, local_session)

            response_signin_init = auth_durak_webapi.signin_init(auth_federate_response, encrypted_a['result'])
            signin_init_json = response_signin_init.json()

            data = {'s': {
                "iterations": signin_init_json['iteration'],
                "serverPublicValue": signin_init_json['b'],
                "salt": signin_init_json['salt'],
                "c": signin_init_json['c'],
                "protocol": "s2k",
                "password": auth_durak_webapi.password
            }}
            complete_data = get_complete_data(data, local_session)

            response_signin_complete = auth_durak_webapi.signin_complete(response_signin_init, complete_data['result']['M1'], data['s']['c'], complete_data['result']['M2'])
            if 'hsa2' not in response_signin_complete.text:
                logger.debug(response_signin_complete.text)
                continue

            auth_durak_webapi.update_x_apple_id_session_id(response_signin_complete)

            response_auth_hsa2 = auth_durak_webapi.appleauth_auth(response_signin_complete)

            # Getting SMS
            code = None
            if config.SMSHUB_SELF_ENTER_CODE:
                code = input('Введите код из СМС: ')
            else:
                set_status_response = smshub.set_status(SetStatus.ACCESS_RETRY_GET, activation_id)
                set_status_text = set_status_response.text

                if set_status_text != SetStatus.ACCESS_RETRY_GET.name:
                    logger.debug(f'SET_STATUS_TEXT is not ACCESS_RETRY_GET: {set_status_text}')

                current_time = datetime.now()
                while not code:
                    elapsed_minutes = (datetime.now() - current_time).total_seconds() / 60
                    if elapsed_minutes > config.SMSHUB_MINUTES_FOR_WAITING_SMS_CODE:
                        break

                    get_status_response = smshub.get_status(activation_id)
                    get_status_text = get_status_response.text
                    if get_status_text.split(':')[0] != 'STATUS_OK':
                        sleep(1)
                    else:
                        code = get_status_text.split(':')[1]

            if not code:
                logger.debug('Не удалось получить код из смс')
                smshub.set_status(SetStatus.ACCESS_CANCEL, activation_id)
                account_number = activation_id = None
                continue
            # Getting SMS

            response_securitycode = auth_durak_webapi.phone_securitycode(response_auth_hsa2, code)
            if 'Incorrect Verification Code' in response_securitycode.text:
                logger.info('Неверный код изи смс, надо бы сделать тут повторный запрос')
                continue

            response_2sv_trust = auth_durak_webapi.auth_2sv_trust(response_securitycode)
            if response_2sv_trust.status_code != 204:
                logger.info(response_2sv_trust.status_code)

            response_oauth_consent = auth_durak_webapi.oauth_consent(response_2sv_trust)
            if response_oauth_consent.status_code != 200:
                logger.info(response_oauth_consent.status_code)

            response_oauth_authorize = auth_durak_webapi.oauth_authorize(response_oauth_consent)
            if response_oauth_authorize.status_code != 200:
                logger.info(response_oauth_authorize.status_code)

                response_consent_complete = auth_durak_webapi.consent_complete(response_oauth_consent)
                if response_consent_complete.status_code != 200:
                    logger.info(response_consent_complete.status_code)

                response_oauth_authorize = auth_durak_webapi.oauth_authorize(response_consent_complete)
                if response_oauth_authorize.status_code != 200:
                    logger.info(response_oauth_authorize.status_code)

            if not (config.SMSHUB_USE_MY_NUMBER or config.SMSHUB_SELF_ENTER_CODE):
                set_status_response = smshub.set_status(SetStatus.ACCESS_RETRY_GET, activation_id)
                set_status_text = set_status_response.text

                if set_status_text != SetStatus.ACCESS_RETRY_GET.name:
                    logger.debug(f'SET_STATUS_TEXT is not ACCESS_RETRY_GET: {set_status_text}')

            apple_id_token = ''
            try:
                apple_id_token = response_oauth_authorize.text.split('"id_token" : "')[1].split('"')[0]
            except Exception as ex:
                logger.exception(f'Ошибка при парсинге apple_id_token: {ex}')
                continue

            durak_tokens = get_tokens_by_apple_id_token(apple_id_token)
            tokens_text = ''
            for token in durak_tokens:
                tokens_text += f'{token}\n'
                logger.info(f'Зарегистрировал и сохранил: {token}')

            with open('reged_tokens.txt', 'a') as file:
                file.write(tokens_text)

            break
            # Authorize APPLE ID to DURAK ONLINE:

    logger.info('Cookies is ended!')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(e)
        input(e)
