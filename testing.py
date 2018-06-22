"""
Module for testing
"""

import os.path
from typing import List, Dict

import json_manager
import agents


def test_reply_agent(agent_function: "agent's function to process input message",
                     test_file_name: str,
                     test_output_file_name: str = 'test_output.json') -> None:
    """
    Test agent that can give replies on text messages
    :param agent_function: agent to test
    :param test_file_name: file with test data
    :param test_output_file_name: file for writing testing output in
    :return: None
    """
    if not (agent_function and test_file_name and test_output_file_name):
        return

    # read lines of text as messages
    with open(test_file_name, 'r', encoding='utf-8-sig') as test_file:
        messages = test_file.readlines()

    # list with dictionaries that contain message text and reply
    test_output: List[Dict[str, str]] = list()

    for message in messages:
        test_output.append({"message": message,
                            "reply": agent_function(message)})

    json_manager.write(test_output, test_output_file_name)


TEST_NUMBERS = [1, 0, 2]

for test_n in TEST_NUMBERS:
    for agent_f in [agents.CONVERSATION_CONTROLLER.proceed_input_message]:
        test_reply_agent(agent_f,
                         os.path.join('data', 'tests', f'test{str(test_n)}.txt'),
                         test_output_file_name=f'test_output_CONVERSATION_CONTROLLER_n_{str(test_n)}.txt')
