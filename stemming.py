"""
Module for stemming Russian words.

https://en.wikipedia.org/wiki/Stemming
"""


from nltk.stem.snowball import RussianStemmer

# object which will stem the word
STEMMER = RussianStemmer()


def stem(word):
    """
    Stems given word using snowball algorithm.
    :param word: string that contains one word
    :return: string that contains stemmed word
    """
    return STEMMER.stem(word)
