"""
Module for text generating
"""
import random
import re
import string
from typing import Dict, List, Set, Callable, Tuple, Any
from time import process_time

from nltk.tokenize import sent_tokenize, word_tokenize

from text_processing import stem, tag_words_by_part_of_speech, PARTS_OF_SPEECH, get_parts_of_speech
import logger


LETTERS_REGEX = '[^\W\d_]'
END_PUNCT_REGEX = '[!.?]'

LOGGER = logger.get_logger(__file__)


def measure_run_time(func: Callable) -> Callable:
    """
    Wrapper for measuring run time of a given function
    :param func: function that will be run
    :return: result of wrapping the function
    """
    def call_and_measure(*args: Tuple, **kwargs: Dict) -> Any:
        """
        Calls function and prints its run time
        :param kwargs: key arguments for calling the function
        :return: returned value of the function
        """
        start_time = process_time()
        result = func(*args, **kwargs)
        print(func.__name__ + ' ' + str(process_time() - start_time))
        return result
    return call_and_measure


class TextGenerator:
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
        self._begin_links: Dict[str, Set[str]] = dict()
        # links for adding words to the end of the text
        self._end_links: Dict[str, Set[str]] = dict()
        # maximum length of the text
        self.max_sent_length = -1
        for sentence in sentences:
            words = word_tokenize(sentence)
            self.max_sent_length = len(words) if len(words) > self.max_sent_length else self.max_sent_length
            self._ends.append(words[-1])
            for word in words:
                self._words.add(word)

        self._begin_links, self._end_links = self._construct_links(sentences)

    def _construct_links(self, sentences: List[str]) -> (Dict[str, Set[str]], Dict[str, Set[str]]):
        """
        Constructs links between words
        :param sentences: sentences from natural language
        :return: begin links and end links
        """

        # links that represent connection between the word and the word before it
        begin_links: Dict[str, Set[str]] = dict()
        # links that represent connection between the word and the word after it
        end_links: Dict[str, Set[str]] = dict()

        for sentence in sentences:
            words = word_tokenize(sentence)
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    current_i = i
                    next_i = i + 1
                    if words[next_i] not in begin_links:
                        begin_links[words[next_i]] = set()
                    begin_links[words[next_i]].add(words[current_i])
                    if words[current_i] not in end_links:
                        end_links[words[current_i]] = set()
                    end_links[words[current_i]].add(words[next_i])

        # adding links from the knowledge base
        for word, previous_links in self._begin_links.items():
            if word not in begin_links:
                begin_links[word] = previous_links
            else:
                for previous_word in previous_links:
                    begin_links[word].add(previous_word)
        for word, next_links in self._end_links.items():
            if word not in end_links:
                end_links[word] = next_links
            else:
                for next_word in next_links:
                    end_links[word].add(next_word)

        return begin_links, end_links

    def _add_end_punct(self, text: str) -> str:
        """
        Adds ending punctuation to the text
        :param text: initial text without ending punctuation
        :return: text with ending punctuation on its end
        """
        return text + random.choice(self._ends)

    def _polish_text(self, text: str) -> str:
        """
        Removes unwanted symbols from the generated text
        :param text: generated text
        :return: polished text
        """
        result = text

        # remove too long punctuation
        unwanted_puncts = re.findall('[' + re.escape(string.punctuation) + ']{4,100}', result)
        for up in unwanted_puncts:
            result = result.replace(up, up[:3])

        # remove paired symbols without pair
        pair_puncts = {
            "''": '``',
            '(': ')',
            '[': ']',
            '{': '}',
            '«': '»'
        }
        for key, value in pair_puncts.items():
            if re.search(re.escape(key), result) and not re.search(re.escape(value), result):
                result = result.replace(key, '')
            elif re.search(re.escape(value), result) and not re.search(re.escape(key), result):
                result = result.replace(value, '')

        result = result.replace(',.', '.')

        # remove empty parenthesis
        empty_pairs = re.findall('(' + re.escape('|'.join(pair_puncts.keys())) + ')' + ' '
                                 + '(' + re.escape('|'.join(pair_puncts.values())) + ')', result)
        for e_p in empty_pairs:
            result = result.replace(e_p, ' ')

        # make the letter before ending punctuation upper case
        low_letters = re.findall(END_PUNCT_REGEX + ' ' + LETTERS_REGEX, result)
        for l_l in low_letters:
            result = result.replace(l_l, l_l[:-1] + l_l[-1].upper())

        # remove unwanted spaces
        spaces = re.findall(' +[' + re.escape("'!#$%&)*+,./:;>?@\\]^_|}~\"") + ']|[' + re.escape('(<@[`{') + '] +',
                            result)
        for sp in spaces:
            result = result.replace(sp, sp.replace(' ', ''))

        result = result.replace('``', '"')
        result = result.replace("''", '"')

        # remove spaces in the begin and in the end of the text
        result = result.strip(' ')

        # make the first letter upper case
        result = result[0].upper() + result[1:]

        # adding ending punctuation if needed
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
        return re.search(check_regex, text)

    def generate(self, start_word: str = None,
                 begin_links: Dict[str, Set[str]] = None,
                 end_links: Dict[str, Set[str]] = None,
                 max_word_num: int = None) -> Set[str]:
        """
        Generates texts
        :param start_word: the word from which the generation starts
        :param begin_links: links from words to the previous ones
        :param end_links: links from words to next ones
        :param max_word_num: max number of words in each generated text
        :return: unique generated texts
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

        max_iter_num = 500

        i = 0
        while variants_stack and i < max_iter_num:
            i += 1
            popped = variants_stack.pop()
            joined = ' '.join(popped)
            if len(popped) < max_word_num:

                # possible additions from the end of the text
                ends = end_links.get(popped[-1], list()).copy()
                for end in ends:
                    variants_stack.append(popped + [end])

                # possible additions from the begin of the text
                begins = begin_links.get(popped[0], list()).copy()
                for begin in begins:
                    variants_stack.append([begin] + popped)

                if self._evaluate_text(joined):
                    result.add(self._polish_text(joined))
                else:
                    random.shuffle(variants_stack)

        return result

    def generate_from_input(self, input_text: str) -> Set[str]:
        """
        Generates text using user's input
        :param input_text: text from user
        :return: unique generated texts
        """
        text = input_text
        if not re.search(END_PUNCT_REGEX, text):
            text = text + '.'

        sentences = sent_tokenize(text)
        result: List[str] = list()

        custom_begin_links, custom_end_links = self._construct_links(sentences)
        start_words = list()

        for sentence in sentences:
            words = word_tokenize(sentence)
            tagged = tag_words_by_part_of_speech(words)
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
        self._pronoun_verb_ending_links = dict()
        lines = base_text.split('\n')
        for line in lines:
            p_o_s_string = self._make_part_of_speech_string(line)
            line_ends = re.findall('|'.join(list(map(re.escape, self._ends))) + '$', line)
            self._text_structures.add(p_o_s_string)
            self._text_structures_ends[p_o_s_string] = self._text_structures_ends.get(p_o_s_string, list()) + line_ends
            self._create_pronoun_verb_ending_links(line)

    @staticmethod
    def _iterate_through_pronoun_with_verb(text: str, f: Callable[[str, str], None]) -> None:
        """
        iterates through each pronoun in the text that has a verb after it
        :param text: text to use
        :param f: function that is called when a needed pronoun and verb are found
        :return: None
        """
        sub_sentence_reg = '(?:' + LETTERS_REGEX + '|[ \-—])+'
        sub_sentences = re.findall(sub_sentence_reg, text)
        for s_s in sub_sentences:
            words = word_tokenize(s_s)
            tagged = tag_words_by_part_of_speech(words)
            pronouns_and_verbs = list(filter(lambda x: x[1] in {PARTS_OF_SPEECH['verb'],
                                                                PARTS_OF_SPEECH['personal pronoun']}, tagged))
            for i, word in enumerate(pronouns_and_verbs):
                current_i = i
                next_i = i + 1
                if current_i < len(pronouns_and_verbs) - 1 \
                        and pronouns_and_verbs[current_i][1] == PARTS_OF_SPEECH['personal pronoun'] \
                        and pronouns_and_verbs[next_i][1] == PARTS_OF_SPEECH['verb']:
                    pronoun = pronouns_and_verbs[current_i][0].lower()
                    verb = pronouns_and_verbs[next_i][0].lower()
                    f(pronoun, verb)

    @staticmethod
    def _get_word_ending(word: str) -> str:
        """
        Gets an ending of the word
        :param word: word
        :return: ending of the word
        """
        return word[len(stem(word)):]

    def _create_pronoun_verb_ending_links(self, text: str) -> None:
        """
        Creates links between pronouns and ending of the verbs after them
        :param text: text to get pronouns and verbs
        :return: None
        """
        links = self._pronoun_verb_ending_links

        def add_pronoun_verb_link(pronoun: str, verb: str) -> None:
            """
            Adds the link
            :param pronoun:
            :param verb:
            :return: None
            """
            link = links.get(pronoun, set())
            link.add(self._get_word_ending(verb))
            links[pronoun] = link

        self._iterate_through_pronoun_with_verb(text, add_pronoun_verb_link)

    def _check_pronoun_verb_endings(self, text: str) -> bool:
        """
        Checks ending of the verb before a pronoun
        :param text: text to get verbs and pronouns from
        :return: indication of validity of verbs
        """
        result = [True]

        def update_check_result(pronoun: str, verb: str) -> None:
            verb_ending = self._get_word_ending(verb)
            result[0] &= pronoun in self._pronoun_verb_ending_links \
                         and verb_ending in self._pronoun_verb_ending_links[pronoun]

        self._iterate_through_pronoun_with_verb(text, update_check_result)

        return result[0]

    def _polish_text(self, text: str) -> str:
        """
        Same as in parent class but some additions
        :param text: initial text
        :return: polished text
        """
        result = super()._polish_text(text)

        # remove dashes from the end of the text
        unwanted_dashes = re.findall(' *[—-]' + END_PUNCT_REGEX + '|' + ' *[—-]$', result)
        for u_d in unwanted_dashes:
            result = result.replace(u_d, u_d.strip(' —-'))

        # replace non-ending symbols with ending punctuation
        ends = re.findall(END_PUNCT_REGEX + '$', result)
        if not ends:
            result = result.rstrip(',:; ') + random.choice(self._ends)

        return result

    @staticmethod
    def _make_part_of_speech_string(text: str) -> str:
        """
        Makes a string that consists of parts of speech names without the ending punctuation
        :param text: natural language text
        :return: produced string
        """
        parts_of_speech = list()
        sentences = sent_tokenize(text)
        for sentence in sentences:
            words = word_tokenize(sentence)
            parts_of_speech += get_parts_of_speech(words)

        return ' '. join(parts_of_speech[:-1] if len(parts_of_speech) > 1
                         and parts_of_speech[-1] == PARTS_OF_SPEECH['other'] else parts_of_speech)

    def _check_text_structure(self, text: str) -> bool:
        """
        Check if the text has the same parts of speech order as in the knowledge base
        :param text: generated text
        :return: indication of text validity
        """
        check_string = self._make_part_of_speech_string(text)
        return check_string in self._text_structures

    def _evaluate_text(self, text) -> bool:
        """
        Check if validity of the text
        :param text: generated text
        :return: indication of text validity
        """
        regex = '^' + LETTERS_REGEX  # for checking if the text starts with a letter
        return self._check_text_structure(text) and self._check_pronoun_verb_endings(text) \
               and re.search(regex, text)

    def _add_end_punct(self, text: str) -> str:
        """
        Adds ending punctuation depending on text structure
        :param text: generated text without ending punctuation
        :return: text with ending punctuation
        """
        p_o_s_string = self._make_part_of_speech_string(text)
        ends = self._text_structures_ends.get(p_o_s_string, None)
        if not ends:
            ends = self._ends
        return text + random.choice(ends)