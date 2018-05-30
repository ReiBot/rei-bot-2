"""
Module for getting nouns from sentence

Note: works for Russian language only
"""


from nltk import pos_tag
from nltk.tokenize import word_tokenize


def get_nouns(sentence):
    """
    Produces nouns
    :param sentence: a text string which contains one sentence
    :return: array of strings, where each string is a noun
    """
    words = word_tokenize(sentence)
    tagged = pos_tag(words, lang='rus')

    nouns = []
    for word, tag in tagged:
        if tag == 'S':
            nouns.append(word.lower())

    return nouns
