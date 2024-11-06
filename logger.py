import logging

class Log:
    def __init__(self):
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def getLogger(self) -> logging.Logger:
        return self.logger