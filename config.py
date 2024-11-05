import configparser
import logging

class ConfigParser:
    def __init__(self, logger: logging.Logger):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.logger = logger
        
    def get_token(self):
        self.logger.info("Токен успешно загружен")
        return self.config['BOT']['TOKEN']