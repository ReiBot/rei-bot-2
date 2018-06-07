"""
This module contains agents that gives text output on given input text
"""

import random
from typing import List, Dict, Optional
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
            if not nouns:
                self.noun_sentences[None].append(sentence)
            else:
                for noun in nouns:
                    # if the noun occurs the first time set an empty array
                    if noun not in self.noun_sentences:
                        self.noun_sentences[noun] = list()
                    self.noun_sentences[noun].append(sentence)

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

    def get_reply(self, input_text: str, no_empty_reply: bool = False,
                  black_list: List[str] = None) -> Optional[str]:
        """
        Returns text output by
        search known nouns in the input text
        and giving predefined phrases as a reply
        :param input_text: text containing natural language
        :param no_empty_reply: flag for omitting empty reply
        :param black_list: replies to be omitted from possible variants
        :return: text with the reply
        """

        sentences = sent_tokenize(input_text)

        reply_variants = list()

        # getting reply variants by taking and stemming all nouns from text
        # and searching for predefined replies containing these nouns
        for sentence in sentences:
            # getting nouns
            nouns = text_processing.get_nouns(sentence)
            for noun in nouns:
                # stemming nouns
                stemmed_noun = text_processing.stem(noun)
                # searching for known nouns
                if stemmed_noun in self.stemmed_nouns:
                    for noun in self.stemmed_nouns[stemmed_noun]:
                        # adding sentences with this noun
                        reply_variants += self.noun_sentences[noun]

        if not reply_variants:
            if no_empty_reply:
                reply_variants = self.noun_sentences[None].copy()
            else:
                return None

        # omitting variants from black list
        for reply in black_list:
            # preventing from deleting everything
            if reply in reply_variants and (not no_empty_reply or len(reply_variants) > 1):
                reply_variants.remove(reply)

        if len(reply_variants) > 1:
            return random.choice(reply_variants)
        elif reply_variants:
            return reply_variants[0]

        return None


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
                knowledge[other_key].remove(reply)

        json_manager.write(self.knowledge_base, self.save_file_name)

    def search_reply(self, input_text: str) -> [str, List[str], None]:
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
                    replies.remove(wrong_reply)
            return random.choices(replies)
        elif black_list:
            return black_list
        return None
