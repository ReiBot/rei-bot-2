"""
Module for getting nouns from Russian sentence
"""


from nltk import pos_tag
from nltk.tokenize import word_tokenize


def get_nouns(sentence):
    """
    Produces nouns using standard NLTK method get_pos()
    with extra parameter lang='rus' to make it work with Russian

    :param sentence: a text string which contains one sentence
    :return: array of strings, where each string is a noun
    """
    words = word_tokenize(sentence)
    tagged = pos_tag(words, lang='rus')

    nouns = list()
    for word, tag in tagged:
        # Checking if a word is a noun because for a noun the tag will be "S"
        if tag == 'S':
            nouns.append(word.lower())

    return nouns
