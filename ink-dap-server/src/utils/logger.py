"""
Конфигурация ведения журнала для адаптера отладки
"""

import logging
import sys


def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """

    Args:
        name: Имя логгера
        level: Уровень ведения журнала

    Возвращает:
        Настроенный экземпляр логгера
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Удаляем существующие обработчики
    logger.handlers.clear()

    # Создаем консольный обработчик
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    # Создаем простой форматер
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger