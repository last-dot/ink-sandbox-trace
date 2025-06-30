"""
Мост к Rust
Обеспечиваем связь с PolkaVM на основе Rust
"""

import subprocess
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class RustBridge:
    """Управляет взаимодействием с процессом Rust"""

    def __init__(self):
        self.logger = logging.getLogger("InkDebugAdapter.RustBridge")
        self.process = None
        self.request_id = 1
        self.pending_requests = {}
        self.reader = None
        self.writer = None

    async def start(self, host: str = "localhost", port: int = 9229):
        """Подключаемся к Rust серверу по TCP."""
        self.logger.info(f"Подключение к Rust серверу {host}:{port}")

        try:
            self.reader, self.writer = await asyncio.open_connection(host, port)
            asyncio.create_task(self._read_responses())
            self.logger.info("Успешно подключились к Rust серверу")
        except Exception as e:
            self.logger.error(f"Не удалось подключиться: {e}")
            raise

    async def call_method(self, method: str, params: Dict[str, Any]) -> Any:
        """Вызовим метод в Rust."""
        if not self.writer:
            raise RuntimeError("Отладчик Rust не запущен")

        request_id = self._next_id()
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        # Send request
        request_json = json.dumps(request) + "\n"
        self.writer.write(request_json.encode())
        await self.writer.drain()

        self.logger.debug(f"Отправлен запрос: {request}")

        # Дожидаемся ответа
        future = asyncio.Future()
        self.pending_requests[request_id] = future

        try:
            response = await asyncio.wait_for(future, timeout=10.0)
            return response
        except asyncio.TimeoutError:
            del self.pending_requests[request_id]
            raise RuntimeError(f"TТаймаут ожидания ответа на {method}")

    async def _read_responses(self):
        """О процессе Rust."""
        while self.reader:
            try:
                line = await self.reader.readline()
                if not line:
                    break

                response = json.loads(line.decode())
                self.logger.debug(f"Получен ответ: {response}")

                # Реакция на обращение
                request_id = response.get("id")
                if request_id and request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)

                    if "error" in response:
                        future.set_exception(RuntimeError(response["error"]))
                    else:
                        future.set_result(response.get("result"))

            except Exception as e:
                self.logger.error(f"Error reading response: {e}")

    async def set_breakpoint(self, address: int) -> bool:
        """Установить точку останова по заданному адресу."""
        result = await self.call_method("setBreakpoint", {
            "address": address
        })
        return result.get("verified", False)

    async def continue_execution(self):
        """Продолжаем исполнение."""
        await self.call_method("continue", {})

    async def step_over(self):
        """Переходим к текущей инструкции."""
        await self.call_method("stepOver", {})

    async def step_in(self):
        await self.call_method("stepIn", {})

    async def step_out(self):
        """Выходим из текущей функции."""
        await self.call_method("stepOut", {})

    async def get_state(self) -> Dict[str, Any]:
        """Получение текущего состояния отладчика."""
        return await self.call_method("getState", {})

    async def shutdown(self):
        """Выключаем Rust."""
        if self.process:
            try:
                await self.call_method("shutdown", {})
                await self.process.wait()
            except Exception as e:
                self.logger.error(f"Ошибка при выключении: {e}")
                self.process.terminate()

    def _next_id(self) -> int:
        """Получение идентификатора следующего запроса"""
        id = self.request_id
        self.request_id += 1
        return id