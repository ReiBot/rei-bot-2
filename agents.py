"""Module with agents"""

import os.path

from texting_ai import RatingLearningAgent, RatingRandomReplyAgent, NounsFindingAgent, ConversationController, \
    AgentPipeline

AGENT_LANGUAGE_PATH = os.path.join('data', 'language')
RANDOM_REPLY_AGENT = RatingRandomReplyAgent(os.path.join(AGENT_LANGUAGE_PATH, 'sentences.json'))
NOUNS_FINDING_AGENT = NounsFindingAgent(os.path.join(AGENT_LANGUAGE_PATH, 'sentences.json'),
                                        os.path.join(AGENT_LANGUAGE_PATH, 'nouns.json'))
LEARNING_AGENT = RatingLearningAgent(os.path.join('data', 'rated_learning_model.json'),
                                     os.path.join('data',
                                                  'learning_model.json'))
AGENTS_PIPELINE = AgentPipeline(LEARNING_AGENT, NOUNS_FINDING_AGENT, RANDOM_REPLY_AGENT)
CONVERSATION_CONTROLLER = ConversationController(AGENTS_PIPELINE)
