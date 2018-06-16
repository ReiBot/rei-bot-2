"""
Telegram bot module
"""

import ssl
import os.path
import time
from configparser import ConfigParser
from aiohttp import web

import telebot
import texting_ai
import logger

CONFIG = ConfigParser()
CONFIG.read(os.path.join('data', 'config.ini'))

# webhook url
URL_BASE = "https://{}:{}".format(CONFIG['server']['ip'], CONFIG.getint('server', 'port'))
URL_PATH = "/{}/".format(CONFIG['telegram bot']['token'])

telebot.logger = logger.get_logger(__file__)

BOT = telebot.TeleBot(CONFIG['telegram bot']['token'])

# server that will listen for new messages
APP = web.Application()

# time for bot to be "typing" in seconds
TYPING_TIME: int = 2


def set_proxy() -> None:
    """
    Sets the proxy
    :return: None
    """
    enabled = CONFIG.getboolean('proxy', 'enabled')
    if enabled:
        address = CONFIG['proxy']['address']
        port = CONFIG['proxy']['port']
        proxy_type = CONFIG['proxy']['type']
        if proxy_type == 'http':
            telebot.apihelper.proxy = {'http': f'http://{address}:{port}'}
        elif proxy_type == 'socks5':
            user = CONFIG['proxy']['user']
            password = CONFIG['proxy']['port']
            telebot.apihelper.proxy = {'https': f'socks5://{user}:{password}@{address}:{port}'}


set_proxy()


async def handle(request: web.Request) -> web.Response:
    """
    Process webhook calls
    :param request: request to handle
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


@BOT.message_handler(commands=['start, ask'])
def start_reply(message: telebot.types.Message) -> None:
    """
    Handler for /start and /ask commands
    Sends message back to user that sent /start or /ask command
    :param message: received message by bot from user
    :return: None
    """
    # TODO for /ask implement replying on previous message
    # if private message
    if message.chat.type == 'private':
        is_reply = False
    else:
        is_reply = True

    reply_message(is_reply, message,
                  texting_ai.PIPELINE.get_reply(message.text, no_empty_reply=True))


# Handle text messages
@BOT.message_handler(func=lambda message: True, content_types=['text'])
def text_reply(message: telebot.types.Message) -> None:
    """
    Handler for private and group text messages from users
    :param message: received message by bot from user
    :return: None
    """
    text = message.text
    is_reply = True
    no_empty_reply = True

    # if private message
    if message.chat.type == 'private':
        is_reply = False
    # TODO add forward handling
    # if group message and not a reply on bot's message
    elif not check_reply(BOT.get_me().id, message):
        no_empty_reply = False

    reply = texting_ai.PIPELINE.get_reply(text, no_empty_reply=no_empty_reply)
    if reply:
        reply_message(is_reply, message, reply)


def check_reply(_id: int, message: telebot.types.Message) -> bool:
    """
    Check if the message is a reply on given user's message
    :param _id: id of a user whose message was replied to
    :param message: message to check
    :return: True if message is a reply False otherwise
    """
    return message.reply_to_message and message.reply_to_message.from_user.id == _id


def reply_message(message: telebot.types.Message, reply: str, is_reply: bool) -> None:
    """
    Sends reply on message
    :param message: input message
    :param reply: text reply on message
    :param is_reply: True if reply_to() method should be used or False if send_message()
    :return: None
    """
    if not reply:
        return

    BOT.send_chat_action(message.chat.id, 'typing')
    time.sleep(TYPING_TIME)

    if is_reply:
        BOT.reply_to(message, reply)
    else:
        BOT.send_message(message.chat.id, reply)


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
