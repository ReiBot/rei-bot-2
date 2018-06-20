"""
Module for processing Russian text
"""

from typing import Set, Tuple
from nltk.stem.snowball import RussianStemmer
from nltk import pos_tag
from nltk.tokenize import word_tokenize
import logger

# object which will stem the word
STEMMER = RussianStemmer()
LOGGER = logger.get_logger(__file__)

# particular cases of stemming
PARTICULAR_STEMMED_CASES = {
    "рей": "рей"
}


def stem(word: str) -> str:
    """
    Stems given word using snowball algorithm.
    :param word: string that contains one word
    :return: stemmed word
    """

    if not word:
        LOGGER.error("input string is empty or None")
        return None
    if not isinstance(word, str):
        LOGGER.error("input value is not a string")
        return None

    return PARTICULAR_STEMMED_CASES.get(word, STEMMER.stem(word))


def get_nouns(sentence: str) -> Set[str]:
    """
    Produces nouns in lower case using standard NLTK method get_pos()
    with extra parameter lang='rus' to make it work with Russian
    :param sentence: a text string which contains one sentence
    :return: found nouns
    """

    if not sentence:
        LOGGER.error("input value is an empty string or None")
        return set()
    if not isinstance(sentence, str):
        LOGGER.error("input value is not a string")
        return set()

    words = word_tokenize(sentence)
    tagged: Tuple[str, str] = pos_tag(words, lang='rus')

    nouns = set()
    for word, tag in tagged:
        # Checking if a word is a noun because for a noun the tag will be "S"
        if tag == 'S':
            nouns.add(word.lower())

    return nouns
