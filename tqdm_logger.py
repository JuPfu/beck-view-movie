import logging

class TqdmLogger:
    """File-like class redirecting tqdm progress bar to given logging logger."""
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def write(self, msg: str) -> None:
        self.logger.info(msg.lstrip("\r"))

    def flush(self) -> None:
        pass
