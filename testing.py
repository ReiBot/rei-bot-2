"""
Module for testing
"""

import os.path
from typing import List, Dict
import json_manager
import texting_ai


def test_reply_agent(agent: 'agent with "get_reply" function',
                     test_file_name: str,
                     test_output_file_name: str = 'test_output.json') -> None:
    """
    Test agent that can give replies on text messages
    :param agent: agent to test
    :param test_file_name: file with test data
    :param test_output_file_name: file for writing testing output in
    :return: None
    """
    if not (agent and test_file_name and test_output_file_name):
        return

    # read lines of text as messages
    with open(test_file_name, 'r', encoding='utf-8-sig') as test_file:
        messages = test_file.readlines()

    # list with dictionaries that contain message text and reply
    test_output: List[Dict[str, str]] = list()

    for message in messages:
        test_output.append({"message": message,
                            "reply": agent.get_reply(message)})

    json_manager.write(test_output, test_output_file_name)


REPLY_AGENT = texting_ai.NounsFindingAgent(os.path.join('data', 'language', 'sentences.json'),
                                           os.path.join('data', 'language', 'nouns.json'))
test_reply_agent(REPLY_AGENT, os.path.join('data', 'tests', 'test0.txt'))
