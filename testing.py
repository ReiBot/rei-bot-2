"""
Module for testing
"""

import json  # FIXME should be replaced with json manager
from typing import List, Dict
import texting_ai


def test_predefined_reply(agent: texting_ai.PredefinedReplyAgent,
                          test_file_name: str, test_output_file_name: str = 'test_output.json'):
    """
    Test agent that uses predefined replies
    :param agent:
    :param test_file_name:
    :param test_output_file_name:
    :return:
    """
    # read lines of text as messages
    with open(test_file_name, 'r', encoding='utf-8-sig') as test_file:
        messages = test_file.readlines()

    # list with dictionaries that contain message text and reply
    test_output: List[Dict[str, str]] = list()

    for message in messages:
        test_output.append({"message": message,
                            "reply": agent.get_predefined_reply(message)})

    # writing to json file
    # json.dump is used instead of json.dumps because of Cyrillic letters
    with open(test_output_file_name, 'w', encoding='utf8') as json_file:
        json.dump(test_output, json_file, ensure_ascii=False, indent=4)
