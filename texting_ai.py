"""
This module contains agents that gives text output on given input text
"""

import json
import random
from typing import List, Dict, Optional
from nltk.tokenize import sent_tokenize
import nouns_finder
import stemming


class PredefinedReplyAgent:
    """
    Class for agent that sends one of the predefined replies or nothing
    """
    def __init__(self, phrases_json_path: str, nouns_json_path: str):
        # get dictionary from json file
        # encoding='utf-8-sig' is used for omitting \ufeff symbol
        # in the beginning of the string after reading from file
        with open(phrases_json_path, 'r', encoding='utf-8-sig') as input_json_file:
            # load data from input json
            phrases_data = json.load(input_json_file)

        # dictionary with words as keys
        # and array of sentences that contain these words
        self.noun_sentences: Dict[str, List[str]] = dict()

        # iterating through phrases data and storing nouns with sentences
        for sentence, nouns in phrases_data.items():
            for noun in nouns:
                # if the noun occurs the first time set an empty array
                if noun not in self.noun_sentences:
                    self.noun_sentences[noun] = list()
                self.noun_sentences[noun].append(sentence)

        with open(nouns_json_path, 'r', encoding='utf-8-sig') as input_json_file:
            # load data from input json
            nouns_data = json.load(input_json_file)

        # dictionary with stemmed forms as keys
        # and lists of possible nouns that can have this stemmed form as values
        self.stemmed_nouns: Dict[str, List[str]] = dict()

        for noun, stemmed in nouns_data.items():
            # if the stemmed form occurs the first time
            # add entry with an empty list
            if stemmed not in self.stemmed_nouns:
                self.stemmed_nouns[stemmed] = list()
            self.stemmed_nouns[stemmed].append(noun)

    def get_predefined_reply(self, input_text: str) -> Optional[str]:
        """
        Returns text output by
        search known nouns in the input text
        and giving predefined phrases as a reply
        :param input_text: text containing natural language
        :return: text with the reply
        """

        sentences = sent_tokenize(input_text)

        reply_variants = list()

        for sentence in sentences:
            nouns = nouns_finder.get_nouns(sentence)
            for noun in nouns:
                stemmed_noun = stemming.stem(noun)
                if stemmed_noun in self.stemmed_nouns:
                    for noun in self.stemmed_nouns[stemmed_noun]:
                        reply_variants += self.noun_sentences[noun]

        if reply_variants:
            if len(reply_variants) > 1:
                reply = random.choice(reply_variants)
            else:
                reply = reply_variants[0]
        else:
            reply = None

        return reply