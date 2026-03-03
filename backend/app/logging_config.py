import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Logging formatter that adds ANSI color codes based on log level."""

    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        levelname = f"{color}{record.levelname:<8}{self.RESET}"
        timestamp = f"{self.DIM}{self.formatTime(record, self.datefmt)}{self.RESET}"
        name = f"{self.DIM}{record.name}{self.RESET}"
        message = record.getMessage()

        # Colorize the message itself for ERROR and above
        if record.levelno >= logging.ERROR:
            message = f"{color}{message}{self.RESET}"

        formatted = f"{timestamp} | {levelname} | {name} | {message}"

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted += f"\n{color}{record.exc_text}{self.RESET}"

        return formatted


def setup_logging(level: str = "INFO") -> None:
    """Configure colored logging for the application."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    # Configure uvicorn loggers to use our formatter
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
        uv_logger.propagate = False
