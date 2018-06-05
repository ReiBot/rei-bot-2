"""
Telegram bot module
"""

from logging import INFO
import ssl
import os.path

from configparser import ConfigParser
from aiohttp import web

import telebot

import texting_ai

CONFIG = ConfigParser()
CONFIG.read('config.ini')

# webhook url
URL_BASE = "https://{}:{}".format(CONFIG['server']['ip'], CONFIG.getint('server', 'port'))
URL_PATH = "/{}/".format(CONFIG['telegram bot']['token'])

telebot.logger.setLevel(INFO)

BOT = telebot.TeleBot(CONFIG['telegram bot']['token'])

# server that will listen for new messages
APP = web.Application()

AGENT = texting_ai.PredefinedReplyAgent(os.path.join('data', 'language', 'sentences'),
                                        os.path.join('data', 'language', 'nouns'))


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


@BOT.message_handler(commands=['start'])
def start_reply(message: telebot.types.Message) -> None:
    """
    Handler for /start command
    Sends message back to user that sent /start command
    :param message: received message by bot from user
    :return: None
    """
    BOT.send_message(message.chat.id, AGENT.get_predefined_reply(message.text, no_empty_reply=True))


@BOT.message_handler(commands=['ask'])
def ask_reply(message: telebot.types.Message) -> None:
    """
    Handler for /ask command
    Replies to user that sent /start command
    :param message: received message by bot from user
    :return: None
    """
    # TODO for /ask implement replying on previous message
    BOT.reply_to(message, AGENT.get_predefined_reply(message.text, no_empty_reply=True))


# Handle text messages
@BOT.message_handler(func=lambda message: True, content_types=['text'])
def text_reply(message: telebot.types.Message):
    """
    Handler for private and group text messages from users
    :param message: received message by bot from user
    :return: None
    """
    text = message.text

    # if private message
    if message.chat.type == 'private':
        BOT.send_message(message.chat.id, AGENT.get_predefined_reply(text, no_empty_reply=True))
    # if reply on bot's message
    elif check_reply(BOT.get_me().id, message):
        BOT.reply_to(message, AGENT.get_predefined_reply(text, no_empty_reply=True))
    # TODO add forward handling
    # if group message
    else:
        reply = AGENT.get_predefined_reply(text)
        if reply:
            BOT.reply_to(message, reply)


def check_reply(_id: int, message: telebot.types.Message) -> bool:
    """
    Check if the message is a reply on given user's message
    :param _id: id of a user whose message was replied to
    :param message: message to check
    :return: True if message is a reply False otherwise
    """
    return message.reply_to_message and message.reply_to_message.from_user.id == _id


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
