import logging
import os
from dotenv import load_dotenv
from main import Main
load_dotenv()

class Filter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s: | %(message)s')


info = logging.FileHandler('system-logs/client/info.log', mode='w')
info.setFormatter(formatter)
info.setLevel(logging.INFO)
info.addFilter(Filter(logging.INFO))
     
warning = logging.FileHandler('system-logs/client/warnings.log', mode='w')
warning.setFormatter(formatter)
warning.setLevel(logging.WARNING)
warning.addFilter(Filter(logging.WARNING))

error = logging.FileHandler('system-logs/client/errors.log', mode='w')
error.setFormatter(formatter)
error.setLevel(logging.ERROR)
error.addFilter(Filter(logging.ERROR))

critical = logging.FileHandler('system-logs/client/criticals.log', mode='w')
critical.setFormatter(formatter)
critical.setLevel(logging.CRITICAL)
critical.addFilter(Filter(logging.CRITICAL))

logger.addHandler(info)
logger.addHandler(warning)
logger.addHandler(error)
logger.addHandler(critical)


if __name__ == '__main__':
    TOKEN = os.getenv('TOKEN')
    bot = Main()
    bot.run(TOKEN, reconnect=True)