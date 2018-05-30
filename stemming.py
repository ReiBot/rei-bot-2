"""
Module for stemming the word.

Stemming is the process of reducing inflected (or sometimes derived)
words to their word stem, base or root form. (c) Wikipedia

Note: works for Russian language only
"""


from nltk.stem.snowball import RussianStemmer

# object which will stem the word
STEMMER = RussianStemmer()


def stem(word):
    """
    Stems the word.
    :param word: string that contains one word
    :return: string that contains stemmed word
    """
    return STEMMER.stem(word)
