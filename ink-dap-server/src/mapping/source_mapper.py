"""
Source code to instructions mapping
Maps source file lines to PolkaVM instruction addresses
"""

import subprocess
import re
import logging
from typing import Dict, Tuple, Optional, List
from pathlib import Path


class SourceMapper:
    """Maps source code lines to instruction addresses."""

    def __init__(self):
        self.logger = logging.getLogger("InkDebugAdapter.SourceMapper")
        # Mapping: (file, line) -> instruction_address
        self.mappings: Dict[Tuple[str, int], int] = {}
        # Reverse mapping: instruction_address -> (file, line)
        self.reverse_mappings: Dict[int, Tuple[str, int]] = {}

    def load_debug_info(self, elf_path: str):
        """
        Load debug information from ELF file using readelf.

        Args:
            elf_path: Path to ELF file
        """
        self.logger.info(f"Loading debug information from: {elf_path}")

        try:
            # Run readelf to get debug line information
            result = subprocess.run(
                ["readelf", "--debug-dump=decodedline", elf_path],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output
            self._parse_readelf_output(result.stdout)

            self.logger.info(f"Loaded {len(self.mappings)} line mappings")

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to run readelf: {e}")
            raise
        except FileNotFoundError:
            self.logger.error("readelf not found. Please install binutils.")
            raise

    def _parse_readelf_output(self, output: str):
        """Parse readelf output to extract line mappings."""
        # Example readelf output:
        # lib.rs                                        8           0x12f1e       48
        # lib.rs                                       30           0x12f32       51

        # Pattern to match readelf output lines
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
        Convert source line to instruction address.

        Args:
            file: Source file name
            line: Line number

        Returns:
            Instruction address or None if not found
        """
        # Try using only filename (not full path)
        filename = Path(file).name
        address = self.mappings.get((filename, line))

        if address is not None:
            self.logger.debug(f"Mapped {filename}:{line} → 0x{address:x}")
        else:
            self.logger.warning(f"No mapping found for {filename}:{line}")

        return address

    def address_to_line(self, address: int) -> Optional[Tuple[str, int]]:
        """
        Convert instruction address to source line.

        Args:
            address: Instruction address

        Returns:
            Tuple of (filename, line) or None if not found
        """
        return self.reverse_mappings.get(address)

    def find_nearest_address(self, file: str, line: int) -> Optional[int]:
        """
        Find nearest mapped address for given line.
        Useful when exact line mapping doesn't exist.

        Args:
            file: Source file name
            line: Line number

        Returns:
            Nearest instruction address or None
        """
        filename = Path(file).name

        # Find all lines for this file
        file_lines = [
            (l, addr) for (f, l), addr in self.mappings.items()
            if f == filename
        ]

        if not file_lines:
            return None

        # Sort by line number
        file_lines.sort(key=lambda x: x[0])

        # Find nearest line
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
                f"Nearest mapping for {filename}:{line} is "
                f"{filename}:{best_line} → 0x{best_addr:x}"
            )

        return best_addr

    def get_file_lines(self, file: str) -> List[int]:
        """
        Get all mapped line numbers for a file.

        Args:
            file: Source file name

        Returns:
            List of line numbers that have mappings
        """
        filename = Path(file).name
        lines = [
            line for (f, line) in self.mappings.keys()
            if f == filename
        ]
        return sorted(lines)

    def apply_address_offset(self, offset: int):
        """
        Apply offset to all addresses.
        Needed when ELF addresses don't match runtime addresses.

        Args:
            offset: Offset to apply (can be negative)
        """
        self.logger.info(f"Applying address offset: {offset:#x}")

        # Create new mappings with offset
        new_mappings = {}
        new_reverse = {}

        for (file, line), addr in self.mappings.items():
            new_addr = addr + offset
            new_mappings[(file, line)] = new_addr
            new_reverse[new_addr] = (file, line)

        self.mappings = new_mappings
        self.reverse_mappings = new_reverse