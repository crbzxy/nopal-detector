"""
Sistema de logging para el detector de nopal.
"""

import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formatter que añade colores a los logs."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logger(name: str = "nopal_detector", level: int = logging.INFO) -> logging.Logger:
    """Configura y devuelve un logger."""
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # Handler para consola
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Formatter con colores si la consola lo soporta
    if sys.stdout.isatty():
        formatter = ColoredFormatter('%(levelname)s: %(message)s')
    else:
        formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def info(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log informativo."""
    if logger is None:
        logger = setup_logger()
    logger.info(msg)


def warn(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log de advertencia."""
    if logger is None:
        logger = setup_logger()
    logger.warning(msg)


def error(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log de error."""
    if logger is None:
        logger = setup_logger()
    logger.error(msg)


def debug(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log de debug."""
    if logger is None:
        logger = setup_logger()
    logger.debug(msg)