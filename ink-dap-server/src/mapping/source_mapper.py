"""
Сопоставление исходного кода с инструкциями
Сопоставление строк исходного файла с адресами инструкций PolkaVM
"""

import subprocess
import re
import logging
from typing import Dict, Tuple, Optional, List
from pathlib import Path


class SourceMapper:
    """Сопоставляет строки исходного кода с адресами инструкций."""

    def __init__(self):
        self.logger = logging.getLogger("InkDebugAdapter.SourceMapper")
        # Mapping: (file, line) -> instruction_address
        self.mappings: Dict[Tuple[str, int], int] = {}
        # Reverse mapping: instruction_address -> (file, line)
        self.reverse_mappings: Dict[int, Tuple[str, int]] = {}

    def load_debug_info(self, elf_path: str):
        """
        Загрузка отладочной информации из ELF-файла с помощью readelf.

        Args:
        elf_path: Путь к ELF-файлу
        """
        self.logger.info(f"Загрузка отладочной информации из: {elf_path}")

        try:
            # Запускаем readelf, чтобы получить информацию о строках отладки
            result = subprocess.run(
                ["readelf", "--debug-dump=decodedline", elf_path],
                capture_output=True,
                text=True,
                check=True
            )

            # Парсим вывод
            self._parse_readelf_output(result.stdout)

            self.logger.info(f"Загружено {len(self.mappings)} line mappings")

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Не удалось запустить readelf: {e}")
            raise
        except FileNotFoundError:
            self.logger.error("readelf не найден. Пожалуйста, установите binutils.")
            raise

    def _parse_readelf_output(self, output: str):
        """Parse readelf  для извлечения отображений строк."""
        # Пример вывода readelf:
        # lib.rs                                        8           0x12f1e       48
        # lib.rs                                       30           0x12f32       51

        # Шаблон для сопоставления строк вывода readelf
        pattern = r'(\S+\.rs)\s+(\d+)\s+0x([0-9a-fA-F]+)'

        for line in output.split('\n'):
            match = re.search(pattern, line)
            if match:
                filename = match.group(1)
                line_num = int(match.group(2))
                address = int(match.group(3), 16)

                # Store mapping
                self.mappings[(filename, line_num)] = address
                self.reverse_mappings[address] = (filename, line_num)

                self.logger.debug(f"Mapped {filename}:{line_num} → 0x{address:x}")

    def line_to_address(self, file: str, line: int) -> Optional[int]:
        """
        Преобразование исходной строки в адрес инструкции.

        Args:
         file: Имя исходного файла
         line: Номер строки

        Возвращает:
            Адрес инструкции или None, если он не найден
        """
        # Пробуем использовать только имя файла (не полный путь)
        filename = Path(file).name
        address = self.mappings.get((filename, line))

        if address is not None:
            self.logger.debug(f"Mapped {filename}:{line} → 0x{address:x}")
        else:
            self.logger.warning(f"No mapping найденный для {filename}:{line}")

        return address

    def address_to_line(self, address: int) -> Optional[Tuple[str, int]]:
        """
        Преобразование адреса инструкции в исходную строку.

        Args:
        address: Адрес инструкции

        Возвращает:
            Кортеж из (filename, line) или None, если не найден.
        """
        return self.reverse_mappings.get(address)

    def find_nearest_address(self, file: str, line: int) -> Optional[int]:
        """
        Находит ближайший сопоставленный адрес для заданной линии.
        Полезно, когда точного отображения линии не существует.

        Args:
         file: Имя исходного файла
         line: Номер строки

        Возвращает:
            Ближайший адрес инструкции или None
        """
        filename = Path(file).name

        # Находим все строки для этого файла
        file_lines = [
            (l, addr) for (f, l), addr in self.mappings.items()
            if f == filename
        ]

        if not file_lines:
            return None

        # Сортируем по номеру строки
        file_lines.sort(key=lambda x: x[0])

        # Находим ближайшую линию
        best_line = None
        best_addr = None
        min_diff = float('inf')

        for mapped_line, addr in file_lines:
            diff = abs(mapped_line - line)
            if diff < min_diff:
                min_diff = diff
                best_line = mapped_line
                best_addr = addr

        if best_addr:
            self.logger.debug(
                f"Ближайшее отображение для {filename}:{line} это "
                f"{filename}:{best_line} → 0x{best_addr:x}"
            )

        return best_addr

    def get_file_lines(self, file: str) -> List[int]:
        """
        Получает все маперы номера строк для файла.

        Args:
        file: Имя исходного файла

        Возвращает:
            Список номеров строк, которые имеют мапер
        """
        filename = Path(file).name
        lines = [
            line for (f, line) in self.mappings.keys()
            if f == filename
        ]
        return sorted(lines)

    def apply_address_offset(self, offset: int):
        """
        Применить смещение ко всем адресам.
        Необходимо, когда адреса ELF не совпадают с адресами времени выполнения.

        Args:
        offset: Смещение для применения (может быть отрицательным)
        """
        self.logger.info(f"Применение смещения адреса: {offset:#x}")

        # Создание новых маперов со смещением
        new_mappings = {}
        new_reverse = {}

        for (file, line), addr in self.mappings.items():
            new_addr = addr + offset
            new_mappings[(file, line)] = new_addr
            new_reverse[new_addr] = (file, line)

        self.mappings = new_mappings
        self.reverse_mappings = new_reverse