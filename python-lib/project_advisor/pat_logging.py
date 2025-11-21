import logging
import dataikuapi

def create_logger(logging_level: str = "DEBUG"):
    """
    logging_level (String): Optional
    logging levels are : CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
    If no logging level is given, the project variable "logging_level" will be used.
    """
    #Format logging messagae
    formatter = logging.Formatter(fmt='Plugin: Project Advisor | [%(levelname)s] : %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Build logger
    logger = logging.getLogger("project_advisor")
    logger.setLevel(logging_level)
    logger.addHandler(handler)
    logger.propagate = False # To avoid double logging
    return logger

def set_logging_level(logger : logging.Logger, plugin_config : dict):
        """
        Set the logging level of logger
        """
        # Plugin (Instance) level config
        logging_level = plugin_config.get("logging_level", "DEBUG")
        logger.setLevel(logging_level)
        logger.info(f"Logging level set to {logging.getLevelName(logger.getEffectiveLevel())}")

# Init logger for all of PAT
logger = create_logger()