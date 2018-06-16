class GradableMessage:
    grade: [-1, 0, 1] = 0
    input_message: str = None
    reply_message: str = None

    def __init__(self, input_message: str, reply_message: str):
        self.input_message = input_message
        self.reply_message = reply_message
