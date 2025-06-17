#!/usr/bin/env python3
"""
Ink! v6 Debug Adapter for VS Code
Main entry point for the debug adapter server
"""

import sys
import asyncio
import logging
from pathlib import Path

# Добавляем src в путь к Python
src_path = Path(__file__).parent / "src"
print(f"Looking for src at: {src_path}")
print(f"Src exists: {src_path.exists()}")
print(f"Src is directory: {src_path.is_dir()}")

# Список содержимого src
if src_path.exists():
    print(f"Contents of src: {list(src_path.iterdir())}")
    adapter_path = src_path / "adapter"
    if adapter_path.exists():
        print(f"Contents of adapter: {list(adapter_path.iterdir())}")

sys.path.insert(0, str(src_path))
print(f"Python path: {sys.path[:2]}")  # Show first 2 paths

try:
    from adapter.debug_adapter import DebugAdapter
    from utils.logger import setup_logger
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {Path.cwd()}")
    raise


async def main():
    """Основная точка входа для отладочного адаптера"""
    # Настройка ведения журнала
    logger = setup_logger("InkDebugAdapter")
    logger.info("Starting Ink! Debug Adapter...")

    try:
        # Создание и запуск отладочного адаптера
        adapter = DebugAdapter()
        await adapter.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Запускаем функцию async main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОтладочный адаптер завершен пользователем", file=sys.stderr)
        sys.exit(0)