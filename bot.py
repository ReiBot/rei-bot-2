"""
Telegram bot module
"""

from logging import INFO
import ssl

from configparser import ConfigParser
from aiohttp import web

import telebot

CONFIG = ConfigParser()

CONFIG.read('config.ini')

# webhook url
URL_BASE = "https://{}:{}".format(CONFIG['server']['ip'], CONFIG.getint('server', 'port'))
URL_PATH = "/{}/".format(CONFIG['telegram bot']['token'])

telebot.logger.setLevel(INFO)

BOT = telebot.TeleBot(CONFIG['telegram bot']['token'])

# server that will listen for new messages
APP = web.Application()


async def handle(request: web.Request) -> web.Response:
    """
    Process webhook calls
    :param request: request to held
    :return: response for sender
    """
    if request.match_info.get('token') == BOT.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        BOT.process_new_updates([update])
        response = web.Response()
    else:
        response = web.Response(status=403)

    return response

APP.router.add_post('/{token}/', handle)


@BOT.message_handler(commands=['start'])
def start_reply(message: telebot.types.Message) -> None:
    """
    Handler for /start command
    :param message: received message
    :return: None
    """
    pass


@BOT.message_handler(commands=['ask'])
def ask_reply(message: telebot.types.Message) -> None:
    """
    Handler for /ask command
    :param message: received message
    :return: None
    """
    pass


# Handle text messages
@BOT.message_handler(func=lambda message: True, content_types=['text'])
def text_reply(message: telebot.types.Message):
    """
    Handler for text messages
    :param message: received message
    :return: None
    """
    pass


# Remove webhook, it fails sometimes the set if there is a previous webhook
BOT.remove_webhook()

# Set webhook
BOT.set_webhook(url=URL_BASE + URL_PATH, certificate=open(CONFIG['ssl']['certificate'], 'r'))

# Build ssl context
CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
CONTEXT.load_cert_chain(CONFIG['ssl']['certificate'], CONFIG['ssl']['private key'])

# Start aiohttp server
web.run_app(
    APP,
    host=CONFIG['server']['ip'],
    port=CONFIG['server']['port'],
    ssl_context=CONTEXT,
)
