"""
Module for testing
"""

import os.path
from typing import List, Dict
import random

import json_manager
import agents
from text_generation import PartsOfSpeechTextGenerator


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


def agent_testing():
    test_numbers = [1, 0, 2]

    for test_n in test_numbers:
        for agent_f in [agents.CONVERSATION_CONTROLLER.proceed_input_message]:
            test_reply_agent(agent_f,
                             os.path.join('data', 'tests', f'test{str(test_n)}.txt'),
                             test_output_file_name=f'test_output_CONVERSATION_CONTROLLER_n_{str(test_n)}.txt')


def text_generating():
    base_path = os.path.join('data', 'text', 'speech_base.txt')
    test_path = os.path.join('data', 'tests', 'test2.txt')

    with open(base_path, 'r') as file:
        text_gen = PartsOfSpeechTextGenerator(file.read())

    with open(test_path, 'r') as file:
        test = file.readlines()

    for i, line in enumerate(test):
        print('in:\t', line)
        replies = text_gen.generate_from_input(line)
        if replies:
            print('out:\t', replies)
        else:
            print('out:\t')
        print()


def dialog_imitation():
    base_path = os.path.join('data', 'text', 'speech_base.txt')
    with open(base_path, 'r') as file:
        text_gen = PartsOfSpeechTextGenerator(file.read())

    while True:
        user_message = input()
        answers = text_gen.generate_from_input(user_message)
        while not answers:
            answers = text_gen.generate()
        print('>>', random.choice(list(answers)))


text_generating()
