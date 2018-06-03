import json
import texting_ai


def test_predefined_reply(agent: texting_ai.PredefinedReplyAgent,
                          test_file_name: str, test_output_file_name:str='test_output.txt'):
    with open(test_file_name, 'r', encoding='utf-8-sig') as test_file:
        messages = test_file.readlines()

    test_output = list()
    for message in messages:
        test_output.append({"message": message,
                            "reply": agent.get_predefined_reply(message),
                            })

    # writing to json file
    # json.dump is used instead of json.dumps because of Cyrillic letters
    with open(test_output_file_name, 'w', encoding='utf8') as json_file:
        json.dump(test_output, json_file, ensure_ascii=False, indent=4)


test_agent = texting_ai.PredefinedReplyAgent('sentences_and_nouns.json', 'nouns_and_stemmed.json')
test_predefined_reply(test_agent, 'data/tests/rei2_test_messages.txt')