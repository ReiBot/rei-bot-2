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
from nltk import pos_tag

from text_processing import stem
import logger

BASE_PATH = os.path.join('data', 'text', 'speech_base.txt')

TEST_PATH = os.path.join('data', 'tests', 'test0.txt')

PARTS_OF_SPEECH = {
        'noun': 'S',
        'verb': 'V',
        'personal pronoun': 'S-PRO',
        'connecting words': 'CONJ',
        'part': 'PART',
        'other': 'NONLEX'
    }

LETTERS_REGEX = '[^\W\d_]'
END_PUNCT_REGEX = '[!.?]'

LOGGER = logger.get_logger(__file__)


def measure_run_time(func):
    def call_and_measure(*args, **kwargs):
        start_time = process_time()
        result = func(*args, **kwargs)
        print(func.__name__ + ' ' + str(process_time() - start_time))
        return result
    return call_and_measure


class TextGenerator:
    def _construct_links(self, sentences: List[str]) -> (Dict[str, List[str]], Dict[str, List[str]]):
        begin_links: Dict[str, List[str]] = dict()
        end_links: Dict[str, List[str]] = dict()

        for sentence in sentences:
            words = word_tokenize(sentence)
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    current_i = i
                    next_i = i + 1
                    begin_links[words[next_i]] = begin_links.get(words[next_i], list()) + [words[current_i]]
                    end_links[words[current_i]] = end_links.get(words[current_i], list()) + [words[next_i]]

        for word, previous_links in self._begin_links.items():
            begin_links[word] = begin_links.get(word, list()) + previous_links
        for word, next_links in self._end_links.items():
            end_links[word] = end_links.get(word, list()) + next_links

        return begin_links, end_links

    def __init__(self, base_text: str):
        """
        :param base_text: text which is used for generation
        """

        lines = base_text.split('\n')
        sentences = []
        for line in lines:
            sentences += sent_tokenize(line)

        # all the words that are used for generation
        self._words: Set[str] = set()
        # possible end for the text
        self._ends: List[str] = list()
        # links for adding words to the begin of the text
        self._begin_links: Dict[str, List[str]] = dict()
        # links for adding words to the end of the text
        self._end_links: Dict[str, List[str]] = dict()
        # maximum length of the text
        self.max_sent_length = -1
        for sentence in sentences:
            words = word_tokenize(sentence)
            self.max_sent_length = len(words) if len(words) > self.max_sent_length else self.max_sent_length
            self._ends.append(words[-1])
            for word in words:
                self._words.add(word)

        self._begin_links, self._end_links = self._construct_links(sentences)

    def _add_end_punct(self, text: str) -> str:
        return text + random.choice(self._ends)

    def _polish_text(self, text: str) -> str:
        result = text

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

        empty_pairs = re.findall('(' + re.escape('|'.join(pair_puncts.keys())) + ')' + ' '
                                 + '(' + re.escape('|'.join(pair_puncts.values())) + ')', result)
        for e_p in empty_pairs:
            result = result.replace(e_p, ' ')

        low_letters = re.findall(END_PUNCT_REGEX + ' ' + LETTERS_REGEX, result)
        for l_l in low_letters:
            result = result.replace(l_l, l_l[:-1] + l_l[-1].upper())

        result = result.replace('``', '"')
        result = result.replace("''", '"')

        spaces = re.findall(' +[' + re.escape("'!#$%&)*+,./:;>?@\\]^_|}~\"") + ']|[' + re.escape('(<?@[`{') + '] +',
                            result)
        for sp in spaces:
            result = result.replace(sp, sp.replace(' ', ''))

        result = result.rstrip(' ')

        return self._add_end_punct(result) \
            if re.search('[^'+re.escape(string.punctuation)+']$', result) else result

    def _evaluate_text(self, text: str) -> bool:
        """
        Checks if the text is complete
        :param text: text to check
        :return: True if complete False otherwise
        """
        # regex to check if the text is complete
        check_regex = f'^{LETTERS_REGEX}.*{END_PUNCT_REGEX}$'

        """
        known_words = list(filter(lambda w: not re.search(END_PUNCT_REGEX, w) and
                                  w in self._words, word_tokenize(text)))
        """
        return re.search(check_regex, text) # and known_words

    def generate(self, start_word: str = None,
                 begin_links: Dict[str, List[str]] = None,
                 end_links: Dict[str, List[str]] = None,
                 max_word_num: int = None) -> Set[str]:
        """
        Generates texts
        :param start_word: the word from which the generation starts
        :param begin_links: links from words to the previous ones
        :param end_links: links from words to next ones
        :param max_word_num: max number of words in each generated text
        :return: unique texts
        """
        variants_stack = list()
        if not start_word:
            variants_stack.append(random.choices(list(self._end_links.keys())))
        else:
            variants_stack.append([start_word])

        if not begin_links:
            begin_links = self._begin_links
        if not end_links:
            end_links = self._end_links
        if not max_word_num:
            max_word_num = self.max_sent_length
        result = set()

        max_stack_num = 1_000

        while variants_stack and len(variants_stack) < max_stack_num:
            popped = variants_stack.pop()
            joined = ' '.join(popped)
            if len(popped) < max_word_num:

                # possible additions from the end of the text
                ends = end_links.get(popped[-1], list()).copy()
                random.shuffle(ends)
                for end in ends:
                    variants_stack.append(popped + [end])

                # possible additions from the begin of the text
                begins = begin_links.get(popped[0], list()).copy()
                random.shuffle(begins)
                for begin in begins:
                    variants_stack.append([begin] + popped)

                if self._evaluate_text(joined):
                    result.add(self._polish_text(joined))
                else:
                    random.shuffle(variants_stack)

        return result

    def generate_from_input(self, input_text: str) -> Set[str]:
        text = input_text
        if not re.search(END_PUNCT_REGEX, text): text = text + '.'

        sentences = sent_tokenize(text)
        result: List[str] = list()

        custom_begin_links, custom_end_links = self._construct_links(sentences)
        start_words = list()

        for sentence in sentences:
            words = word_tokenize(sentence)
            tagged = pos_tag(words, lang='rus')
            important_words = list(filter(lambda t_w: t_w[1] in {PARTS_OF_SPEECH['noun'],
                                                                 PARTS_OF_SPEECH['personal pronoun'],
                                                                 PARTS_OF_SPEECH['verb']}, tagged))
            start_words += list(map(lambda w: w[0], important_words))

        stemmed = set(map(stem, start_words))
        extra_words = list(filter(lambda word: stem(word) in stemmed, self._words))
        start_words += extra_words

        for word in set(start_words):
            result += self.generate(start_word=word, begin_links=custom_begin_links, end_links=custom_end_links)

        return set(result)


class PartsOfSpeechTextGenerator(TextGenerator):
    """
    Same as its parent but evaluates text using order of parts of speech got from speech base
    """
    def __init__(self, base_text):
        super().__init__(base_text)
        self._text_structures: Set[str] = set()
        self._text_structures_ends: Dict[str, List[str]] = dict()
        lines = base_text.split('\n')
        for line in lines:
            p_o_s_string = self._make_part_of_speech_string(line)
            line_ends = re.findall('|'.join(list(map(re.escape, self._ends))) + '$', line)
            self._text_structures.add(p_o_s_string)
            self._text_structures_ends[p_o_s_string] = self._text_structures_ends.get(p_o_s_string, list()) + line_ends

    def _polish_text(self, text: str):
        result = super()._polish_text(text)
        unwanted_dashes = re.findall(' *[—-]' + END_PUNCT_REGEX + '|' + ' *[—-]$', result)
        for u_d in unwanted_dashes:
            result = result.replace(u_d, u_d.strip(' —-'))

        ends = re.findall(END_PUNCT_REGEX + '$', result)
        if not ends:
            result = result.rstrip(',:; ') + random.choice(self._ends)

        return result

    @staticmethod
    def _make_part_of_speech_string(text: str) -> str:
        parts_of_speech = list()
        sentences = sent_tokenize(text)
        for sentence in sentences:
            words = word_tokenize(sentence)
            tagged = pos_tag(words, lang='rus')
            parts_of_speech += list(map(lambda t: t[1].split('=')[0], tagged))

        return ' '. join(parts_of_speech[:-1] if len(parts_of_speech) > 1
                         and parts_of_speech[-1] == PARTS_OF_SPEECH['other'] else parts_of_speech)

    def _evaluate_text(self, text):
        check_string = self._make_part_of_speech_string(text)
        return check_string in self._text_structures  # and super()._evaluate_text(text)

    def _add_end_punct(self, text: str) -> str:
        p_o_s_string = self._make_part_of_speech_string(text)
        ends = self._text_structures_ends.get(p_o_s_string, None)
        if not ends:
            ends = self._ends
        return text + random.choice(ends)

    def generate_from_input(self, input_text: str):
        return super().generate_from_input(input_text)


def main():
    with open(BASE_PATH, 'r') as file:
        text_gen = PartsOfSpeechTextGenerator(file.read())

    with open(TEST_PATH, 'r') as file:
        test = file.readlines()

    for i, line in enumerate(test):
        print('in:\t', line)
        replies = text_gen.generate_from_input(line)
        if replies:
            print('out:\t', replies)
        else:
            print('out:\t')
        print()


if __name__ == '__main__':
    main()
