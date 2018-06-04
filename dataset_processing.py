"""
Module for converting data set into files used by agent
"""

from nltk.tokenize import sent_tokenize
import json_manager
import nouns_finder
import stemming


def read_text_file(file_name: str) -> str:
    """
    Reads file and returns its text
    :param file_name: name of a file to read
    :return: text of the file
    """
    # encoding='utf-8-sig' is used for omitting \ufeff symbol
    # in the beginning of the string after reading from file
    with open(file_name, 'r', encoding='utf-8-sig') as text_file:
        text = text_file.read()

    return text


def write_sentences_and_nouns(text_file_name: str,
                              json_file_name: str = "sentences_and_nouns.json") -> None:
    """
    Reads text file and writes json with with object containing sentences as attributes
    and lists of nouns in corresponding sentence as values.
    :param text_file_name: name of the input text file
    :param json_file_name: name of the output json file
    :return: None
    """

    # read text
    input_text = read_text_file(text_file_name)

    # sentences in the text
    sentences = sent_tokenize(input_text)

    # dictionary to serialized for json
    sentences_and_nouns = dict()

    # searching for nouns
    for sentence in sentences:
        print(sentence)
        nouns = nouns_finder.get_nouns(sentence)
        # set is not json-serializable so has to be converted to list
        sentences_and_nouns[sentence] = list(nouns)

    # writing to json file
    json_manager.write(sentences_and_nouns, json_file_name)


def write_nouns_and_stemmed(input_json_name="sentences_and_nouns.json",
                            output_json_name="nouns_and_stemmed.json") -> None:
    """
    Writes json with nouns and their stemmed forms
    from json with sentences and nouns
    :param input_json_name: file name of json with sentences and nouns
    :param output_json_name: file name of json with nouns and their stemmed forms
    :return: None
    """

    input_data = json_manager.read(input_json_name)

    nouns_and_stemmed = dict()

    # iterating through input data and storing nouns with stemmed forms
    for _, nouns in input_data.items():
        for noun in nouns:
            nouns_and_stemmed[noun] = stemming.stem(noun)

    json_manager.write(nouns_and_stemmed, output_json_name)
