import logging

import click_log

from ._cli import steinbock_cmd_group
from ._steinbock import logger

# click_log.basic_config(logger=logger)
logger_handler = click_log.ClickHandler()
logger_handler.formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger.handlers = [logger_handler]
logger.propagate = False

if __name__ == "__main__":
    steinbock_cmd_group(prog_name="steinbock")
