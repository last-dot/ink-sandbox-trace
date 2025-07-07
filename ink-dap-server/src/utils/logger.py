"""
Конфигурация ведения журнала для адаптера отладки
Логи идут и в stderr и в файл debug_adapter.log
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Установка логгера с выводом в stderr и в файл.

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

    # Создаем форматер
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Консольный обработчик (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файловый обработчик
    try:
        # Определяем путь к лог файлу (рядом с main.py)
        log_file = Path(__file__).parent.parent / "debug_adapter.log"

        # Создаем файловый обработчик (перезаписывает файл при каждом запуске)
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Логируем успешное создание файла
        logger.info(f"Логи также сохраняются в файл: {log_file}")

    except Exception as e:
        # Если не удалось создать файл - продолжаем только с консольным логированием
        logger.warning(f"Не удалось создать лог файл: {e}")

    return logger