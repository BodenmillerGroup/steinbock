import logging

logger = logging.getLogger(__name__.rpartition(".")[0])


class SteinbockException(Exception):
    pass
