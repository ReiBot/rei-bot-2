"""Module for operating on telegram messages"""

from telebot.types import Message
from typing import Set

import logger

LOGGER = logger.get_logger(__file__)
CURRENT_GRADING_MESSAGE = None


class GradableMessage:
    """
    For storing information about grading message which is used for agent learning
    """

    # attribute that represents 'grade' of the reply on message based on ratio of likes and dislikes
    # where -1 is for dislikes > likes 0 is for equality and 1 is for likes > dislikes
    _grade: [-1, 0, 1] = 0

    _likes_n: int = 0
    _dislikes_n: int = 0

    def __init__(self, message: Message, reply_message: str):
        self._users_liked: Set[int] = set()
        self._users_disliked: Set[int] = set()
        self.message = message
        self.input_message = message.text
        self.reply_message = reply_message

    def _update_likes(self, user_id):
        if user_id in self._users_liked:
            self._likes_n -= 1
            self._users_liked.remove(user_id)
        else:
            self._likes_n += 1
            self._users_liked.add(user_id)
            if user_id in self._users_disliked:
                self._update_dislikes(user_id)

    def _update_dislikes(self, user_id):
        if user_id in self._users_disliked:
            self._dislikes_n -= 1
            self._users_disliked.remove(user_id)
        else:
            self._dislikes_n += 1
            self._users_disliked.add(user_id)
            if user_id in self._users_liked:
                self._update_likes(user_id)

    def update_grade(self) -> bool:
        """
        Updates grade of the message
        :return: True if the grade was changed else False
        """
        old_grade = self._grade
        if self._likes_n > self._dislikes_n:
            self._grade = 1
        elif self._likes_n < self._dislikes_n:
            self._grade = -1
        else:
            self._grade = 0

        return True if self._grade != old_grade else False

    def up_vote(self, user_id: int) -> None:
        """
        Handles up-voting action made by a user
        :param user_id: id of a voted user
        :return: None
        """
        self._update_likes(user_id)

    def down_vote(self, user_id: int) -> None:
        """
        Handles down-voting action made by a user
        :param user_id: id of a voted user
        :return: None
        """
        self._update_dislikes(user_id)

    def get_likes(self) -> int:
        """
        Gets number of likes
        :return: number of likes
        """
        return self._likes_n

    def get_dislikes(self) -> int:
        """
        Gets number of dislikes
        :return: number of dislikes
        """
        return self._dislikes_n

    def get_grade(self) -> int:
        """
        Gets the grade of the message
        :return: grade
        """
        return self._grade
