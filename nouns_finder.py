"""
Module for getting nouns from Russian sentence
"""


from nltk import pos_tag
from nltk.tokenize import word_tokenize

import logger

LOGGER = logger.get_logger(__file__)


def get_nouns(sentence: str) -> set:
    """
    Produces nouns in lower case using standard NLTK method get_pos()
    with extra parameter lang='rus' to make it work with Russian

    :param sentence: a text string which contains one sentence
    :return: set of strings, where each string is a noun
    """

    if not sentence:
        LOGGER.error("input value is an empty string or None")
        return set()
    if not isinstance(sentence, str):
        LOGGER.error("input value is not a string")
        return set()

    words = word_tokenize(sentence)
    tagged = pos_tag(words, lang='rus')

    nouns = set()
    for word, tag in tagged:
        # Checking if a word is a noun because for a noun the tag will be "S"
        if tag == 'S':
            nouns.add(word.lower())

    return nouns
