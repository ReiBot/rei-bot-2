"""
Module for reading and writing json files
"""

import json
from typing import Dict, TypeVar, List

T = TypeVar('T', List, Dict)


def read(file_name: str) -> T:
    """
    Reads json file
    :param file_name: name of file to read
    :return: data from json string read from file
    """

    # encoding='utf-8-sig' is used for omitting \ufeff symbol
    # in the beginning of the string after reading from file
    with open(file_name, 'r', encoding='utf-8-sig') as file:
        # load data from json file as dictionary
        data = json.load(file)

    return data


def write(data: T, file_name: str) -> None:
    """
    Writes to json file
    :param data: data to write
    :param file_name: name of a file to write
    :return: None
    """

    # json.dump is used instead of json.dumps because of Cyrillic letters
    with open(file_name, 'w', encoding='utf8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
