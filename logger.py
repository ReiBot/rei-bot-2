"""
Module for logging
"""
import logging
from logging.handlers import TimedRotatingFileHandler

# Path to write
LOG_FILE_PATH = 'data/logs/logs.txt'


def get_logger(tag: str) -> object:
    """
    Produces logger with given message tag
    which will write logs to the console and file stored in LOG_FILE_PATH directory
    :param tag: tag for messages of the logger
    :return: logger object
    """

    logger = logging.getLogger(tag)
    logger.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    file_handler = TimedRotatingFileHandler(LOG_FILE_PATH,
                                            when='midnight', interval=1, backupCount=1)
    file_handler.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - ' + tag + ': %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
