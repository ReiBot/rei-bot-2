"""
Telegram bot module
"""

import time
import os.path
import ssl
from configparser import ConfigParser
from typing import Callable

import telebot
import emoji
from aiohttp import web

import logger
import messages
import agents

CONFIG = ConfigParser()
CONFIG.read(os.path.join('data', 'config.ini'))

# webhook url
URL_BASE = "https://{}:{}".format(CONFIG['server']['ip'], CONFIG.getint('server', 'port'))
URL_PATH = "/{}/".format(CONFIG['telegram bot']['token'])

telebot.logger = logger.get_logger(__file__)

LOGGER = telebot.logger

BOT = telebot.TeleBot(CONFIG['telegram bot']['token'])

# server that will listen for new messages
APP = web.Application()

# time for bot to be "typing" in seconds
TYPING_TIME: int = 2

PRIVATE_MESSAGE = 'private'
TYPING = 'typing'
DOWN_VOTE = 'down vote'
UP_VOTE = 'up vote'

# date of the bot start
START_DATE = time.time()
MESSAGE_ACTUALITY_PERIOD = 6*60*60*60  # six hours in seconds


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


def check_message_actuality(actuality_period: int) -> Callable:
    """
    Wrapper that checks if the group message is not too old to handle it
    :param actuality_period: [seconds] period that limits the age of user's message
    :return: wrapped handler
    """
    def wrap(func: Callable) -> Callable:
        """
        :param func: handler for Telegram messages
        """
        def check_and_handle_message(message: telebot.types.Message) -> None:
            """
            Ignores messages that were sent when the bot was not working
            except the ones that were sent not earlier that given period
            :param message: message to handle
            :return: None
            """
            if message and isinstance(message, telebot.types.Message) and message.chat.type != PRIVATE_MESSAGE:
                difference = START_DATE - message.date
                difference = difference if difference >= 0 else actuality_period
                if difference > actuality_period:
                    return None
            return func(message)
        return check_and_handle_message
    return wrap


@BOT.message_handler(commands=['ask'])
@check_message_actuality(MESSAGE_ACTUALITY_PERIOD)
def command_reply(message: telebot.types.Message) -> None:
    """
    Handler for /ask command
    Sends message back to user that sent /ask command
    :param message: received message by bot from user
    :return: None
    """
    # TODO for /ask implement replying on previous message

    is_private = message.chat.type == PRIVATE_MESSAGE
    reply_message(message,
                  agents.CONVERSATION_CONTROLLER.proceed_input_message(message.text,
                                                                       is_private, True),
                  not is_private)


@BOT.message_handler(func=lambda message: True, content_types=['text'])
@check_message_actuality(MESSAGE_ACTUALITY_PERIOD)
def text_reply(message: telebot.types.Message) -> None:
    """
    Handler for private and group text messages from users
    :param message: received message by bot from user
    :return: None
    """
    text = message.text
    is_private = message.chat.type == PRIVATE_MESSAGE
    is_reply = check_reply(BOT.get_me().id, message)
    as_reply = True if not is_private else False
    # indicates if the message is directed to the bot
    is_directed = is_private or is_reply

    # ignore messages that were send when the bot was not working
    # except ones that were directed to bot
    if not is_directed and message.date < START_DATE:
        return

    reply = agents.CONVERSATION_CONTROLLER.proceed_input_message(text, is_directed, False)
    if reply:
        reply_message(message, reply, as_reply)


def check_reply(_id: int, message: telebot.types.Message) -> bool:
    """
    Check if the message is a reply on given user's message
    :param _id: id of a user whose message was replied to
    :param message: message to check
    :return: True if message is a reply False otherwise
    """
    if message.reply_to_message:
        return message.reply_to_message.from_user.id == _id

    return False


def make_voting_keyboard(likes: int, dislikes: int) -> telebot.types.InlineKeyboardMarkup:
    """
    Makes inline keyboard for grading message by likes and dislikes
    :param likes: number of likes to display
    :param dislikes: number of dislikes to display
    :return: keyboard that can be attached to message
    """
    keyboard = telebot.types.InlineKeyboardMarkup()
    callback_button_dislike = telebot.types.InlineKeyboardButton(
        text=f"{emoji.emojize(':thumbs_down:')} {dislikes}",
        callback_data=DOWN_VOTE)
    callback_button_like = telebot.types.InlineKeyboardButton(
        text=f"{emoji.emojize(':thumbs_up:')} {likes}",
        callback_data=UP_VOTE)
    keyboard.row(callback_button_dislike, callback_button_like)

    return keyboard


def remove_inline_keyboard(message: telebot.types.Message) -> None:
    """
    Removes inline keyboard from message
    :param message: the message a keyboard to be removed from
    :return: None
    """
    # handling connection errors
    try:
        BOT.edit_message_reply_markup(chat_id=message.chat.id,
                                      message_id=message.message_id, reply_markup=None)
    except Exception as error:
        LOGGER.error(error)


def reply_message(message: telebot.types.Message, reply: str, is_reply: bool) -> None:
    """
    Sends reply on message
    :param message: input message
    :param reply: text reply on message
    :param is_reply: True if reply_to() method should be used or False if send_message()
    :return: None
    """

    if not reply:
        LOGGER.error("empty reply in reply_message()")
        return

    # removing keyboard from previous message
    if messages.CURRENT_GRADING_MESSAGE:
        old_message: telebot.types.Message = messages.CURRENT_GRADING_MESSAGE.message
        remove_inline_keyboard(old_message)

    BOT.send_chat_action(message.chat.id, TYPING)
    time.sleep(TYPING_TIME)

    keyboard = make_voting_keyboard(0, 0)

    if is_reply:
        new_message = BOT.reply_to(message, reply, reply_markup=keyboard)
    else:
        new_message = BOT.send_message(message.chat.id, reply, reply_markup=keyboard)

    messages.CURRENT_GRADING_MESSAGE = messages.GradableMessage(new_message, message.text)


@BOT.callback_query_handler(func=lambda call: True)
def callback_inline(call: telebot.types.CallbackQuery) -> None:
    """Callback that
    is executed when a user presses a button on the message inline keyboard"""

    if call.data in {DOWN_VOTE, UP_VOTE}:
        grading_message: messages.GradableMessage = messages.CURRENT_GRADING_MESSAGE
        message: telebot.types.Message = call.message

        # if the message is not the one that is currently grading
        # then remove keyboard
        if not grading_message or message.message_id != grading_message.message.message_id:
            remove_inline_keyboard(message)
            return

        user_id = call.from_user.id

        if call.data == UP_VOTE:
            grading_message.up_vote(user_id)
        elif call.data == DOWN_VOTE:
            grading_message.down_vote(user_id)

        grading_message.update_grade()

        # attaching keyboard to message
        keyboard = make_voting_keyboard(grading_message.get_likes_num(),
                                        grading_message.get_dislikes_num())
        BOT.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id,
                                      reply_markup=keyboard)

        # learning
        agents.LEARNING_AGENT.rating_learn(grading_message.input_message,
                                           grading_message.reply_message,
                                           grading_message.get_change_difference())

    BOT.answer_callback_query(call.id)


# Remove webhook, it fails sometimes the set if there is a previous webhook
BOT.remove_webhook()


# Set webhook
URL = URL_BASE + URL_PATH
BOT.set_webhook(url=URL, certificate=open(CONFIG['ssl']['certificate'], 'rb'), max_connections=10)

# Build ssl context
CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
CONTEXT.load_cert_chain(CONFIG['ssl']['certificate'], CONFIG['ssl']['private key'])

# Start aiohttp server
web.run_app(
    APP,
    host=CONFIG['server']['listen'],
    port=CONFIG['server']['port'],
    ssl_context=CONTEXT,
)
