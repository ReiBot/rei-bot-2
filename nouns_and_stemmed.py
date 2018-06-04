"""
This module takes json file produced by sentences_and_nouns module
and produces json with object containing words as attributes
and their stemmed forms as values
"""

import json
import stemming


def write_nouns_and_stemmed(input_json_name="sentences_and_nouns.json",
                            output_json_name="nouns_and_stemmed.json") -> None:

    # get dictionary from json file
    # encoding='utf-8-sig' is used for omitting \ufeff symbol
    # in the beginning of the string after reading from file
    with open(input_json_name, 'r', encoding='utf-8-sig') as input_json_file:
        # load data from input json
        input_data = json.load(input_json_file)

    nouns_and_stemmed = dict()

    # iterating through input data and storing nouns with stemmed forms
    for _, nouns in input_data.items():
        for noun in nouns:
            nouns_and_stemmed[noun] = stemming.stem(noun)

    # writing to json file
    # json.dump is used instead of json.dumps because of Cyrillic letters
    with open(output_json_name, 'w', encoding='utf8') as json_file:
        json.dump(nouns_and_stemmed, json_file, ensure_ascii=False, indent=4)
