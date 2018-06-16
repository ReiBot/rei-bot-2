"""Module for operating on telegram messages"""

import telebot.types
import logger

LOGGER = logger.get_logger(__file__)


class GradableMessage:
    """
    For storing information about grading message which is used for agent learning
    """

    # attribute that represents 'grade' of the reply on message based on ratio of likes and dislikes
    # where -1 is for dislikes > likes 0 is for equality and 1 is for likes > dislikes
    grade: [-1, 0, 1] = 0

    def __init__(self, message: telebot.types.Message, reply_message: str):
        if message.content_type == 'text':
            self.message = message
            self.input_message = message.text
            self.reply_message = reply_message
        else:
            LOGGER.error('Wrong message content type')
