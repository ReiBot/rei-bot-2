# ReiBot2

![rei pic](https://i.imgur.com/2DrrJ2Ym.jpg?1)

Chatbot for telegram groups representing anime character [Ayanami Rei](https://en.wikipedia.org/wiki/Rei_Ayanami).

The main purpose of the bot is to entertain members of the group by sending text messages.

The bot is implemented using [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) for sending and receiving messages in [Telegram](https://telegram.org/) and [NLTK](https://github.com/nltk/nltk) for processing incoming messages using part of speech tagging. The bot will search for known nouns and reply with phrases that contain them. It also can receive message evaluation of the last sent message, remember it and consider in the future. 
