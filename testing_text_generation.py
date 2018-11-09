"""
Module for testing text generating objects (TextGenerator class and its descendants)
"""

import os
import unittest

from text_generation import PartsOfSpeechTextGenerator

TEXT_GENERATING_CLASSES = [PartsOfSpeechTextGenerator]

TEST_NUMBERS = [5]

BASE_PATH = os.path.join('data', 'text', 'speech_base.txt')


class TestTextGenerating(unittest.TestCase):
    """
    Class for testing text generation objects' methods that produce generated messages using text message as an input
    """
    def test_text_generating(self) -> None:
        """
        Tests text generation by giving the generator text messages from test files and printing the replies
        :return: None
        """

        for text_generating_class in TEXT_GENERATING_CLASSES:
            with open(BASE_PATH, 'r') as file:
                text_gen = text_generating_class(file.read())
            for test_n in TEST_NUMBERS:
                test_path = os.path.join('data', 'tests', f'test{test_n}.txt')

                with open(test_path, 'r') as file:
                    test = file.readlines()

                for line in test:
                    print('in:\t', line)
                    replies = text_gen.generate_from_input(line)
                    if replies:
                        print('out:\t', replies)
                    else:
                        print('out:\t')
                    print()


if __name__ == '__main__':
    unittest.main()
