"""
Module for slicing text into sentences.
"""

from typing import List
from nltk.tokenize import sent_tokenize
import logger

LOGGER = logger.get_logger(__file__)


def get_sentences(text: str) -> List[str]:
    """
    Splits text into sentences using standard NLTK method sent_tokenize()
    :param text: string containing natural language in written form
    :return: list of strings where each string is a sentence
    """
    if not text:
        LOGGER.error("input string is empty or None")
        return str()
    if not isinstance(text, str):
        LOGGER.error("input value is not a string")
        return str()

    return sent_tokenize(text)
