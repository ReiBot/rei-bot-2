"""
This module contains agents that gives text output on given input text
"""

import random
import time
from typing import List, Dict, Optional, Type
import os.path
import re
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag
import text_processing
import json_manager


class NounsFindingAgent:
    """
    Class for agent that sends one of the predefined replies or nothing
    depending on nouns in the input
    """

    # TODO: implement agent for this
    #  min number of other messages between messages sent by bot
    MESSAGES_PERIOD = 10

    # TODO: remove that to bot module as "typing"
    # seconds to sleep before sending a message
    SLEEP_TIME = 2

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

        # for omitting repeating replies
        # TODO implement agent for that
        self.last_used_reply = None

        # for decreasing frequency of messages sent by bot
        # TODO remove that to bot module as "typing"
        self.message_counter = self.MESSAGES_PERIOD

    def get_reply(self, input_text: str, no_empty_reply: bool = False,
                  black_list: Optional[List[str]] = None) -> Optional[str]:
        """
        Returns text output by
        search known nouns in the input text
        and giving predefined phrases as a reply
        :param input_text: text containing natural language
        :param no_empty_reply: flag for omitting empty reply
        :param black_list: replies to be omitted from possible variants
        :return: text with the reply
        """

        if not input_text:
            return None

        self.message_counter += 1

        if not no_empty_reply and self.message_counter <= self.MESSAGES_PERIOD:
            return None

        words = word_tokenize(input_text)

        stemmed_words = list(map(text_processing.stem, words))

        reply_variants = list()

        # getting reply variants by checking each word if it is known
        for stemmed_word in stemmed_words:
            if stemmed_word in self.stemmed_nouns:
                for noun in self.stemmed_nouns[stemmed_word]:
                    # adding sentences with this noun
                    reply_variants += self.noun_sentences[noun]

        if not reply_variants:
            if no_empty_reply:
                reply_variants = self.noun_sentences[None].copy()
            else:
                return None

        # omitting variants from black list
        if black_list:
            for reply in reply_variants:
                if reply in black_list and (not no_empty_reply or len(reply_variants) > 1):
                    reply_variants.remove(reply)

        # choosing reply which was not used before by checking last_used_reply attribute
        result_reply = None
        if reply_variants:
            if no_empty_reply and len(reply_variants) == 1:
                result_reply = reply_variants[0]
            else:
                while True:
                    result_reply = random.choice(reply_variants)
                    reply_variants.remove(result_reply)

                    if result_reply != self.last_used_reply:
                        break
                    elif not reply_variants:
                        result_reply = None
                        break

        if result_reply:
            # for permitting bot from being banned by telegram
            # because of too frequent messages sent
            # TODO: implement agent for this
            time.sleep(self.SLEEP_TIME)
            self.last_used_reply = result_reply
            self.message_counter = 0

        return result_reply


class LearningAgent:
    """Agent that learns what to say
    depending on user's evaluation of replies given by replying agent"""

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

    def sentence_to_pattern(self, sentence: str) -> str:
        """
        Makes regex pattern out of sentence
        by getting all nouns and verbs and joining them into one string
        :param sentence: input sentence
        :return: regex string
        """

        nouns_and_verbs = list()

        tagged = pos_tag(word_tokenize(sentence), lang='rus')
        for word, tag in tagged:
            # S is for nouns and V is for verbs
            if tag in ['S', 'V']:
                nouns_and_verbs.append(text_processing.stem(word))

        return self.pattern_delimiter.join(nouns_and_verbs)

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
            pattern = self.sentence_to_pattern(sentence)

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

    def get_reply(self, input_text: str) -> [str, List[str], None]:
        """
        Searches for patterns in knowledge base
        that match input text and returns the results of search
        :param input_text: input text to search in
        :return: reply if it is found, black list of replies or None if nothing is found
        """

        patterns = self.knowledge_base.keys()

        replies = list()
        black_list = list()

        # for each known pattern check if the input matches
        for pattern in patterns:
            if re.search(pattern, input_text, re.I):
                # if there no replies for matched pattern but there are non-empty black list
                # then add this information
                if 'replies' not in self.knowledge_base[pattern] \
                        or not self.knowledge_base['replies'] and self.knowledge_base['black list']:
                    black_list += self.knowledge_base['black list']
                else:
                    replies += self.knowledge_base[pattern]['replies']

        # if there are possible replies the remove the ones
        # that are in the black list and return random reply
        if replies:
            for wrong_reply in black_list:
                if wrong_reply in replies:

                    # remove ALL occurrences of wrong reply from replies
                    replies = list(filter(lambda a: a != wrong_reply, replies))
            return random.choices(replies)
        elif black_list:
            return black_list
        return None


# for adapting kwargs to arguments used by agents
AGENT_ADAPTERS: Dict[Type, 'function'] = dict()
AGENT_ADAPTERS[NounsFindingAgent] = lambda **kwargs:\
    (kwargs.input_text, kwargs.no_empty_reply, kwargs.black_list)
AGENT_ADAPTERS[LearningAgent] = lambda **kwargs: kwargs.input_text

# for calling agents' methods that process input message
AGENT_CALLERS: Dict[Type, 'function'] = dict()
AGENT_CALLERS[NounsFindingAgent] = lambda **kwargs:\
    kwargs.agent.get_reply(*AGENT_ADAPTERS[NounsFindingAgent](kwargs))
AGENT_CALLERS[LearningAgent] = lambda **kwargs:\
    kwargs.agent.get_reply(*AGENT_ADAPTERS[LearningAgent](kwargs))


class AgentPipeline:
    """
    Pipeline that iteratively uses agents in order to get reply on input text
    """
    @staticmethod
    def _agent_controller(**kwargs) -> Dict:
        """
        Calls agent with arguments extracted from kwargs using agent callers
        and returns updated kwargs with new values that gives agent
        :param kwargs: arguments for agent
        :return: updated kwargs
        """
        type_key = {
            str: 'reply',
            List[str]: 'black_list',
            bool: 'no_empty_reply'
        }

        if not kwargs.reply:
            result = AGENT_CALLERS[type(kwargs.agent)](kwargs)

            if result:
                result_type = type(result)
                if result_type in type_key:
                    # updating list by adding new elements
                    if isinstance(result, list):
                        kwargs[type_key[result_type]].extend(result)
                    else:
                        kwargs[type_key[result_type]] = result

        return kwargs

    def __init__(self, *args):
        """
        :param args: agents that will be in pipeline
        """
        self.agents = args

    def get_reply(self, input_text: str, no_empty_reply: bool) -> Optional[str]:
        """
        Pass arguments through each of agents and
        returns reply on input text
        :param input_text: input text
        :param no_empty_reply: flag that is True when non-empty reply
        is mandatory and False otherwise
        :return: text reply on input text
        """

        # dictionary for saving updated value in kwargs by its type
        kwargs = {
            'reply': None,
            'input_text': input_text,
            'no_empty_reply': no_empty_reply
        }

        # iterating through agents and passing kwargs through each one
        for agent in self.agents:
            kwargs['agent'] = agent
            # update kwargs by assignment new value got from agent
            kwargs = self._agent_controller(kwargs)

        return kwargs.reply
