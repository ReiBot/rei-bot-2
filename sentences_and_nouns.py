"""
This module takes text file with Russian text and produces json file
with sentences from the text and corresponding nouns for each sentence
"""

import json
import text_to_sentences
import nouns_finder


def write_sentences_and_nouns(text_file_name: str,
                              json_file_name: str = "sentences_and_nouns.json") -> None:
    """
    Reads text file and writes json with with object containing sentences as attributes
    and lists of nouns in corresponding sentence as values.
    :param text_file_name: name of the input text file
    :param json_file_name: name of the output json file
    :return: None
    """

    if not (text_file_name and json_file_name):
        # TODO add error logging
        return

    # encoding='utf-8-sig' is used for omitting \ufeff symbol
    # in the beginning of the string after reading from file
    with open(text_file_name, 'r', encoding='utf-8-sig') as text_file:
        input_text = text_file.read()

    if not input_text:
        # TODO add error logging
        return

    # sentences in the text
    sentences = text_to_sentences.get_sentences(input_text)

    # dictionary to serialized for json
    sentences_and_nouns = dict()

    # searching for nouns
    for sentence in sentences:
        print(sentence)
        nouns = nouns_finder.get_nouns(sentence)
        # set is not json-serializable so has to be converted to list
        sentences_and_nouns[sentence] = list(nouns)

    print(sentences_and_nouns)

    # writing to json file
    # json.dump is used instead of json.dumps because of Cyrillic letters
    with open(json_file_name, 'w', encoding='utf8') as json_file:
        json.dump(sentences_and_nouns, json_file, ensure_ascii=False, indent=4)
