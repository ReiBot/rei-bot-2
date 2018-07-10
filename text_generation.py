"""
Module for text generating
"""

import os.path
import random
import re
import string
from typing import Dict, List, Set
from time import process_time

from nltk.tokenize import sent_tokenize, word_tokenize

from text_processing import stem
import logger

BASE_PATH = os.path.join('data', 'text', 'speech_base.txt')

TEST_PATH = os.path.join('data', 'tests', 'test0.txt')

PARTS_OF_SPEECH = {
        'noun': 'S',
        'verb': 'V',
        'personal pronoun': 'S-PRO',
        'connecting words': 'CONJ',
        'other': 'NONLEX'
    }

LOGGER = logger.get_logger(__file__)


class TextGenerator:
    @staticmethod
    def construct_links(sentences: List[str]) -> (Dict[str, List[str]], Dict[str, List[str]]):
        begin_links: Dict[str, List[str]] = dict()
        end_links: Dict[str, List[str]] = dict()

        for sentence in sentences:
            words = word_tokenize(sentence)
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    begin_links[words[i + 1]] = begin_links.get(words[i + 1], list()) + [words[i]]
                    end_links[words[i]] = end_links.get(words[i], list()) + [words[i + 1]]

        return begin_links, end_links

    def __init__(self, base_text: str):
        """
        :param base_text: text wich is used for generation
        """

        sentences = sent_tokenize(base_text)

        self.words: Set[str] = set()
        self.ends: Set[str] = set()
        self.begin_links: Dict[str, List[str]] = dict()
        self.end_links: Dict[str, List[str]] = dict()
        self.max_sent_length = -1
        for sentence in sentences:
            words = word_tokenize(sentence)
            self.max_sent_length = len(words) if len(words) > self.max_sent_length else self.max_sent_length
            self.ends.add(words[-1])
            for word in words:
                self.words.add(word)

        self.begin_links, self.end_links = self.construct_links(sentences)

    @staticmethod
    def _polish_text(text: str) -> str:
        spaces = re.findall(' [' + re.escape("'!#$%&)*+,./:;>?@\\]^_|}~") + ']|[' + re.escape('(<?@[`{') + '] ', text)
        result = text
        for sp in spaces:
            result = result.replace(sp, sp.replace(' ', ''))

        unwanted_puncts = re.findall('[' + re.escape(string.punctuation) + ']{4,100}', result)
        for up in unwanted_puncts:
            result = result.replace(up, up[:3])

        result = result[0].upper() + result[1:]

        pair_puncts = {
            "''": '``',
            '(': ')',
            '[': ']',
            '{': '}'
        }

        for key, value in pair_puncts.items():
            if re.search(re.escape(key), result) and not re.search(re.escape(value), result):
                result = result.replace(key, '')
            elif re.search(re.escape(value), result) and not re.search(re.escape(key), result):
                result = result.replace(value, '')

        result = result.replace(',.', '.')

        return result + '.' if re.search('[^'+re.escape(string.punctuation)+']$', result) else result

    def generate(self, n: int = 25, start_word: int = None,
                 begin_links: Dict[str, List[str]] = None,
                 end_links: Dict[str, List[str]] = None,
                 max_sentence_length: int = None,
                 ends: Set[str] = None) -> Set[str]:
        """
        Generates texts
        :param n: max number of replies
        :param start_word: the word from which the generation starts
        :param begin_links: links from words to the previous ones
        :param end_links: links from words to next ones
        :param max_sentence_length: max number of words in each generated text
        :param ends: possible ends of text
        :return: unique texts
        """
        variants_stack = list()
        if not start_word:
            variants_stack.append(random.choices(list(self.end_links.keys())))
        else:
            variants_stack.append([start_word])

        if not ends:
            if begin_links or end_links:
                LOGGER.error("There must be ends if there are begin_links or end_links")
                return set()
            ends = self.ends

        if not begin_links:
            begin_links = self.begin_links
        if not end_links:
            end_links = self.end_links
        if not max_sentence_length:
            max_sentence_length = self.max_sent_length
        result = set()

        end_regex = '^[а-яА-Я].*(' + '|'.join(list(map(re.escape, ends))) + ")$"

        start_time = process_time()
        while variants_stack and len(result) < n:
            popped = variants_stack.pop()
            joined = ' '.join(popped)
            if len(popped) < max_sentence_length:

                ends = end_links.get(popped[-1], list()).copy()
                random.shuffle(ends)
                for end in ends:
                    variants_stack.append(popped + [end])

                begins = begin_links.get(popped[0], list()).copy()
                random.shuffle(begins)
                for begin in begins:
                    variants_stack.append([begin] + popped)

                if re.search(end_regex, joined):
                    result.add(self._polish_text(joined))

            if process_time() - start_time > 1: break

        return result

    def generate_from_input(self, input_text: str) -> Set[str]:
        text = input_text

        sentences = sent_tokenize(text)
        result: List[str] = list()

        custom_begin_links, custom_end_links = self.construct_links(sentences)
        start_words = list(custom_end_links.keys())

        for word, previous_links in self.begin_links.items():
            custom_begin_links[word] = custom_begin_links.get(word, list()) + previous_links
        for word, next_links in self.end_links.items():
            custom_end_links[word] = custom_end_links.get(word, list()) + next_links

        ends = set()

        for end in self.ends:
            ends.add(end)

        for sentence in sentences:
            words = word_tokenize(sentence)
            ends.add(words[-1])
            stemmed = set(map(stem, words))
            extra_words = list(filter(lambda word: stem(word) in stemmed, self.words))
            if not extra_words:
                return set()
            else:
                start_words += extra_words

        start_words = list(filter(lambda word: not re.search('[' + re.escape(string.punctuation) + ']', word), start_words))

        for word in set(start_words):
            result += self.generate(start_word=word, begin_links=custom_begin_links, end_links=custom_end_links,
                                    ends=ends, max_sentence_length=10)

        return set(result)


def main():
    with open(BASE_PATH, 'r') as file:
        text_gen = TextGenerator(file.read())

    with open(TEST_PATH, 'r') as file:
        tests = file.readlines()

    for i, test in enumerate(tests):
        texts = text_gen.generate_from_input(test)
        print('input:')
        print('\t'+test)
        print('output:')
        if texts:
            print('\t'+random.choice(list(texts))+'\n')
        else:
            print('\n')


if __name__ == '__main__':
    main()
