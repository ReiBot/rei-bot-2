"""
Module for stemming Russian words.

https://en.wikipedia.org/wiki/Stemming
"""


from nltk.stem.snowball import RussianStemmer
import logger

# object which will stem the word
STEMMER = RussianStemmer()
LOGGER = logger.get_logger(__file__)


def stem(word: str) -> str:
    """
    Stems given word using snowball algorithm.
    :param word: string that contains one word
    :return: string that contains stemmed word
    """

    if not word:
        LOGGER.error("input string is empty or None")
        return str()
    if not isinstance(word, str):
        LOGGER.error("input value is not a string")
        return str()

    return STEMMER.stem(word)
