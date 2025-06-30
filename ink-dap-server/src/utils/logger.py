"""
Конфигурация ведения журнала для адаптера отладки
"""

import logging
import sys
from colorlog import ColoredFormatter


def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Установка цветного регистратора для отладочного адаптера,

    Args:
     name: Имя логера
     level: Уровень ведения журнала

    Возвращает:
        Настроенный экземпляр логгера
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Удаляем существующие обработчики
    logger.handlers.clear()

    # Создаем консольный обработчик с цветным выводом
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    # Создаем цветной форматер
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s:%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger