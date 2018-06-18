"""
This module contains agents that gives text output on given input text
"""

import os.path
import random
import re
from typing import List, Dict, Optional, Type, Tuple

from nltk import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize

import json_manager
import logger
import text_processing

LOGGER = logger.get_logger(__file__)


class NounsFindingAgent:
    """
    Class for agent that sends one of the predefined replies or nothing
    depending on nouns in the input
    """

    def __init__(self, phrases_json_path: str, nouns_json_path: str):
        # load data from input json
        phrases_data = json_manager.read(phrases_json_path)

        # dictionary with words as keys
        # and array of sentences that contain these words
        self.noun_sentences: Dict[Optional[str], List[str]] = dict()

        # for sentences without nouns
        self.noun_sentences[None] = list()

        # iterating through phrases data and storing nouns with sentences
        for sentence, nouns in phrases_data.items():
            if nouns:
                for noun in nouns:
                    # if the noun occurs the first time set an empty array
                    if noun not in self.noun_sentences:
                        self.noun_sentences[noun] = list()
                    self.noun_sentences[noun].append(sentence)
            else:
                # add sentence without nouns
                self.noun_sentences[None].append(sentence)

        # load data from input json
        nouns_data = json_manager.read(nouns_json_path)

        # dictionary with stemmed forms as keys
        # and lists of possible nouns that can have this stemmed form as values
        self.stemmed_nouns: Dict[str, List[str]] = dict()

        for noun, stemmed in nouns_data.items():
            # if the stemmed form occurs the first time
            # add entry with an empty list
            if stemmed not in self.stemmed_nouns:
                self.stemmed_nouns[stemmed] = list()
            self.stemmed_nouns[stemmed].append(noun)

    def get_replies(self, input_text: str,
                    black_list: Optional[List[str]] = None) -> Tuple[List[str]]:
        """
        Returns possible text outputs by
        search known nouns in the input text
        and giving predefined phrases as a reply
        :param input_text: text containing natural language
        :param black_list: replies to be omitted from possible variants
        :return: possible reply variants
        """

        if not input_text:
            return list(),

        words = word_tokenize(input_text)

        stemmed_words = list(map(text_processing.stem, words))

        reply_variants = list()

        # getting reply variants by checking each word if it is known
        for stemmed_word in stemmed_words:
            if stemmed_word in self.stemmed_nouns:
                LOGGER.info(f'"{stemmed_word}" is found in "{input_text}" text')
                for noun in self.stemmed_nouns[stemmed_word]:
                    # adding sentences with this noun
                    reply_variants += self.noun_sentences[noun]

        # omitting variants from black list
        if black_list:
            for reply in black_list:
                if reply in reply_variants:
                    reply_variants = list(filter(lambda x: x != reply, reply_variants))

        return reply_variants,


class LearningAgent:
    """Agent that learns what to say
    depending on user's evaluation of replies given by replying agent"""
    _parts_of_speech = {
        'noun': 'S',
        'verb': 'V',
        'personal pronoun': 'S-PRO',
        'connecting words': 'CONJ',
        'other': 'NONLEX'
    }

    def _is_simple(self, tagged_words: List[Tuple[str, str]]) -> bool:
        # are there any punctuation symbols other than in the end?
        punctuation_symbols = \
            list(filter(lambda tagged_word: tagged_word[1] == self._parts_of_speech['other'],
                        tagged_words))
        if len(punctuation_symbols) > 1 or len(punctuation_symbols) == 1 \
                and tagged_words[-1] != punctuation_symbols[0]:
            return False

        # are there any connecting words (союзы)?
        connecting_words = \
            list(filter(lambda tagged_word: tagged_word[1]
                        == self._parts_of_speech['connecting words'],
                        tagged_words))
        return False if connecting_words else True

    def __init__(self, save_file_name: str):
        """
        :param save_file_name: name of a json file to write learned information
        """

        self.pattern_delimiter = '.*'

        self.save_file_name = save_file_name

        if os.path.isfile(save_file_name):
            self.knowledge_base = json_manager.read(save_file_name)
        else:
            self.knowledge_base: Dict[str, Dict[str, List[str]]] = dict()
            json_manager.write(self.knowledge_base, save_file_name)

    def _sentence_to_pattern(self, sentence: str) -> Optional[str]:
        """
        Makes regex pattern out of sentence
        by getting all nouns, verbs and personal pronouns
        and joining them into one string
        :param sentence: input sentence
        :return: regex string or None if it's impossible to make one
        """

        parts_of_speech = list()

        tagged = pos_tag(word_tokenize(sentence), lang='rus')

        # is sentence simple?
        if not self._is_simple(tagged):
            return None

        for word, tag in tagged:
            if tag in [self._parts_of_speech['noun'], self._parts_of_speech['verb'],
                       self._parts_of_speech['personal pronoun']]:
                parts_of_speech.append(text_processing.stem(word))

        # is there anything to make pattern from?
        if not parts_of_speech:
            return None

        return self.pattern_delimiter.join(parts_of_speech)

    def learn(self, input_text: str, reply: str, right: bool) -> None:
        """
        learns what is right or wrong to say
        :param input_text: text of input message
        :param reply: reply given by replying agent
        :param right: True if agent should learn that given combination of
        sentence pattern and reply is right or False if wrong
        :return: None
        """

        # for right wrong cases
        key = 'replies' if right else 'black list'
        other_key = 'black list' if right else 'replies'

        sentences = sent_tokenize(input_text)

        # each sentence in the text is converted to regex pattern and the information
        # about right/wrong reply is added to knowledge base with this pattern as key
        for sentence in sentences:
            pattern = self._sentence_to_pattern(sentence)

            if not pattern:
                break

            if right:
                LOGGER.info(f'"{pattern}" is learned with reply "{reply}"')
            else:
                LOGGER.info(f'"{pattern}" is learned with prohibited reply "{reply}"')

            if pattern not in self.knowledge_base:
                self.knowledge_base[pattern] = dict()
            knowledge = self.knowledge_base[pattern]

            if key not in knowledge:
                knowledge[key] = list()
            knowledge[key].append(reply)

            if other_key in knowledge and reply in knowledge[other_key]:
                # remove ALL occurrences of reply
                knowledge[other_key] = list(filter(lambda a: a != reply, knowledge[other_key]))

        json_manager.write(self.knowledge_base, self.save_file_name)

    def get_replies(self, input_text: str) -> Tuple[List[str], List[str]]:
        """
        Gets allowed and prohibited replies by searching for patterns in knowledge base
        that match input text
        :param input_text: input text to search in
        :return: allowed and prohibited replies
        """

        patterns = self.knowledge_base.keys()

        replies = list()
        black_list = list()

        # for each known pattern check if the input matches
        for pattern in patterns:
            if re.search(pattern, input_text, re.I):
                LOGGER.info(f'"{pattern}" pattern is found in "{input_text}" text')

                # if there no replies for matched pattern but there are non-empty black list
                # then add this information
                if 'replies' in self.knowledge_base[pattern]:
                    replies += self.knowledge_base[pattern]['replies']
                if 'black list' in self.knowledge_base[pattern]:
                    black_list += self.knowledge_base[pattern]['black list']

        # removing replies from black list
        for wrong_reply in black_list:
            if wrong_reply in replies:
                # remove ALL occurrences of wrong reply from replies
                replies = list(filter(lambda a: a != wrong_reply, replies))

        return replies, black_list


class AgentPipeline:
    """
    Pipeline that iteratively uses agents in order to get reply on input text
    """

    def _agent_controller(self, **kwargs) -> Dict:
        """
        Calls agent with arguments extracted from kwargs using agent callers
        and returns updated kwargs with new values that gives agent
        :param kwargs: arguments for agent caller
            'reply': str
                Reply got from agent,
            'black_list': List[str]
                Prohibited replies,
            'no_empty_reply': bool
                flag for omitting empty reply,
            'agent': [LearningAgent, NounsFindingAgent]
                Agent that processes input and returns reply
        :return: updated kwargs
        """

        updated_kwargs = kwargs.copy()

        agent_type = type(kwargs.get('agent', None))
        # value to be updated in kwargs
        result = self._kwargs_converter[agent_type](*(self._agent_callers[agent_type](**kwargs)),
                                                    kwargs)

        for key, value in result.items():
            updated_kwargs[key] = value

        return updated_kwargs

    def __init__(self, *args: [LearningAgent, NounsFindingAgent]):
        """
        :param args: agents that will be in pipeline
        """
        self.agents = args

        # for adapting kwargs to arguments used by agents
        self._agent_adapters: Dict[Type, 'function'] = dict()
        self._agent_adapters[NounsFindingAgent] = lambda **kwargs: \
            (kwargs.get('input_text', None),
             kwargs.get('black_list', None))
        self._agent_adapters[LearningAgent] = lambda **kwargs: (kwargs.get('input_text', None),)
        self._agent_adapters[RandomReplyAgent] = lambda **kwargs: \
            (kwargs.get('reply_variants', None),
             kwargs.get('black_list', None),
             kwargs.get('no_empty_reply', False))

        # for calling agents' methods that process input message
        self._agent_callers: Dict[Type, 'function'] = dict()
        self._agent_callers[NounsFindingAgent] = lambda **kwargs: \
            kwargs.get('agent', None).get_replies(*self._agent_adapters[NounsFindingAgent](**kwargs))
        self._agent_callers[LearningAgent] = lambda **kwargs: \
            kwargs.get('agent', None).get_replies(*self._agent_adapters[LearningAgent](**kwargs))
        self._agent_callers[RandomReplyAgent] = lambda **kwargs: \
            kwargs.get('agent', None).get_reply(*self._agent_adapters[RandomReplyAgent](**kwargs))

        # for converting agent's output to kwargs parameter(s)
        self._kwargs_converter: Dict[Type, 'function'] = dict()
        self._kwargs_converter[NounsFindingAgent] = lambda replies, kwargs:\
            {'reply_variants': kwargs['reply_variants'] + replies}
        self._kwargs_converter[LearningAgent] = lambda replies, black_list, kwargs:\
            {'reply_variants': kwargs['reply_variants'] + replies,
             'black_list': kwargs['black_list'] + black_list}
        self._kwargs_converter[RandomReplyAgent] = lambda reply, kwargs:\
            {'reply': reply}

    def get_reply(self, input_text: str, no_empty_reply: bool = False) -> Optional[str]:
        """
        Passes arguments through each of agents and
        returns reply on input text
        :param input_text: input text
        :param no_empty_reply: flag that is True when non-empty reply
        is mandatory and False otherwise
        :return: text reply on input text or None if there are no reply on given input
        """

        # initial values for kwargs
        init_kwargs = {
            'reply': None,
            'reply_variants': list(),
            'input_text': input_text,
            'no_empty_reply': no_empty_reply,
            'black_list': list()
        }

        kwargs = init_kwargs

        # iterating through agents and passing kwargs through each one
        for agent in self.agents:
            kwargs['agent'] = agent
            
            # update kwargs by assignment new value got from agent
            kwargs = self._agent_controller(**kwargs)

        return kwargs.get('reply', None)


class RandomReplyAgent:
    """
    Agent that chooses random replies from given ones
    """
    def __init__(self, path_to_phrases: str):
        if not (path_to_phrases or os.path.isfile(path_to_phrases)):
            LOGGER.error('wrong phrases path for RandomReplyAgent')
            return

        self.all_phrases = list(json_manager.read(path_to_phrases).keys())
        self.max_weight = len(self.all_phrases)
        # for multiplying weight of a given reply
        self.given_reply_multiplier = 2
        self.phrases_weights: Dict[str, int] = dict()
        for phrase in self.all_phrases:
            self.phrases_weights[phrase] = self.max_weight

    def get_reply(self, replies: List[str], black_list: List[str], no_empty_reply: bool) -> Tuple[Optional[str]]:
        """
        Gets random reply or nothing if there are no possible replies
        :param replies: given replies
        :param black_list: prohibited replies
        :param no_empty_reply: flag to indicate that there must be a non-empty reply
        as a returned value
        :return: one chosen reply or None
        """
        possible_replies = self.all_phrases if no_empty_reply else replies
        if not possible_replies:
            return None,

        if black_list:
            possible_replies = list(filter(lambda x: x not in black_list, possible_replies))

        if possible_replies:
            reply = random.choices(possible_replies, weights=list(map(
                lambda phrase:
                self.max_weight*self.given_reply_multiplier if phrase in replies else
                self.phrases_weights[phrase], possible_replies)))[0]
            self.phrases_weights[reply] -= 1
            if self.phrases_weights[reply] == 0:
                self.phrases_weights[reply] = self.max_weight
        else:
            reply = None

        return reply,


AGENT_LANGUAGE_PATH = os.path.join('data', 'language')
LEARNING_AGENT = LearningAgent(os.path.join('data', 'learning_model.json'))
RANDOM_REPLY_AGENT = RandomReplyAgent(os.path.join(AGENT_LANGUAGE_PATH, 'sentences.json'))
NOUNS_FINDING_AGENT = NounsFindingAgent(os.path.join(AGENT_LANGUAGE_PATH, 'sentences.json'),
                                        os.path.join(AGENT_LANGUAGE_PATH, 'nouns.json'))
PIPELINE = AgentPipeline(LEARNING_AGENT, NOUNS_FINDING_AGENT, RANDOM_REPLY_AGENT)
