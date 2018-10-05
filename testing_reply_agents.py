"""
Module for testing replying agents (agents that produce reply to the text message)
"""

import os.path
from typing import List, Dict
import unittest

import json_manager
import agents

AGENTS_REPLY_FUNCTIONS = [agents.CONVERSATION_CONTROLLER.proceed_input_message]

TEST_NUMBERS = [1, 0, 2]


class TestReplyAgents(unittest.TestCase):
    """
    Class for testing replying agents' methods that gives reply on the text message
    """
    def test_reply_agents(self) -> None:
        """
        Tests agents that can give replies on text messages by giving to them text messages from files
        and saving the replies to the corresponding output file
        :return: None
        """

        for test_n in TEST_NUMBERS:
            for agent_function in AGENTS_REPLY_FUNCTIONS:
                with self.subTest(test_n=test_n, agent_function=agent_function):
                    test_file_name = os.path.join('data', 'tests', f'test{str(test_n)}.txt')
                    test_output_file_name = f'test_output_{agent_function.__self__.__class__}_n_{str(test_n)}.txt'
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


if __name__ == '__main__':
    unittest.main()
