"""
Module for slicing text into sentences.
"""

from nltk.tokenize import sent_tokenize


def get_sentences(text):
    """
    Splits text into sentences using standard NLTK method sent_tokenize()
    :param text: string containing natural language in written form
    :return: list of strings where each string is a sentence
    """
    return sent_tokenize(text)
