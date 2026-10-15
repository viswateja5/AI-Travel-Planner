import logging
from pathlib import Path


class AppLogger:
    def __init__(self, name: str = "travel_planner") -> None:
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def get_logger(self) -> logging.Logger:
        return self.logger
