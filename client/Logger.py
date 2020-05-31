import logging
import yaml


class Logger:
    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.propagate = False
            console = logging.StreamHandler()
            logger.addHandler(console)
            log_format = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
            formatter = logging.Formatter(log_format)
            console.setFormatter(formatter)
            try:
                with open("appsettings.yaml", "r") as config_file:
                    config = yaml.safe_load(config_file)['logger']
            except FileNotFoundError as e:
                logger.error("FileNotFoundError: ", e)
                raise
            if config['log_level'].upper() == 'INFO':
                console.setLevel(logging.INFO)
                logger.setLevel(logging.INFO)
            elif config['log_level'].upper() == 'DEBUG':
                console.setLevel(logging.DEBUG)
                logger.setLevel(logging.DEBUG)
            else:
                logger.error("Wrong logging level!")
                raise ValueError("Wrong logging level!")
        return logger
