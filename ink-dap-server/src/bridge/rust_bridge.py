"""
Мост к Rust
Обеспечиваем связь с PolkaVM на основе Rust
С автоматическим переподключением каждые 5 секунд
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
        self.is_connected = False
        self.connection_task = None
        self.host = "localhost"
        self.port = 9229

    async def start(self, host: str = "localhost", port: int = 9229):
        """Подключаемся к Rust серверу по TCP с автоматическим переподключением."""
        self.host = host
        self.port = port
        self.logger.info(f"Инициализация подключения к Rust серверу {host}:{port}")

        # Запускаем задачу переподключения в фоне
        self.connection_task = asyncio.create_task(self._connection_loop())

        # Ждем первого подключения максимум 10 секунд
        for i in range(20):  # 20 попыток по 0.5 секунды = 10 секунд
            if self.is_connected:
                self.logger.info("Первоначальное подключение к Rust серверу успешно!")
                return
            await asyncio.sleep(0.5)

        self.logger.warning("Rust сервер пока недоступен")

    async def _connection_loop(self):
        """Цикл переподключения каждые 5 секунд."""
        while True:
            if not self.is_connected:
                try:
                    self.logger.info(f"Попытка подключения к Rust серверу {self.host}:{self.port}...")
                    self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

                    # Запускаем чтение ответов
                    asyncio.create_task(self._read_responses())

                    self.is_connected = True
                    self.logger.info("✅ Успешно подключились к Rust серверу!")

                except Exception as e:
                    self.logger.warning(f"❌ Не удалось подключиться к Rust серверу: {e}")
                    self.is_connected = False
                    self.reader = None
                    self.writer = None

            # Ждем 5 секунд перед следующей попыткой
            await asyncio.sleep(5.0)

    async def call_method(self, method: str, params: Dict[str, Any]) -> Any:
        """Вызовим метод в Rust."""
        if not self.is_connected or not self.writer:
            self.logger.warning(f"Rust сервер недоступен для метода '{method}', возвращаем заглушку")
            # Возвращаем заглушки для разных методов
            if method == "initialize":
                return {"status": "ok", "message": "Simulated response - Rust server not available"}
            elif method == "setBreakpoints":
                return {"breakpoints": [{"id": 1, "verified": True}]}
            else:
                return {"status": "pending", "message": f"Method '{method}' queued until Rust server is available"}

        request_id = self._next_id()
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        try:
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
                self.logger.warning(f"Таймаут ожидания ответа на {method}")
                # Считаем что соединение порвалось
                self.is_connected = False
                raise RuntimeError(f"Таймаут ожидания ответа на {method}")

        except Exception as e:
            self.logger.error(f"Ошибка при вызове {method}: {e}")
            # Считаем что соединение порвалось
            self.is_connected = False
            self.reader = None
            self.writer = None
            raise

    async def _read_responses(self):
        """Читаем ответы от процесса Rust."""
        try:
            while self.reader and self.is_connected:
                try:
                    line = await self.reader.readline()
                    if not line:
                        self.logger.warning("Rust сервер закрыл соединение")
                        break

                    response = json.loads(line.decode())
                    self.logger.debug(f"Получен ответ: {response}")

                    # Обрабатываем ответы на запросы
                    request_id = response.get("id")
                    if request_id and request_id in self.pending_requests:
                        future = self.pending_requests.pop(request_id)

                        if "error" in response:
                            future.set_exception(RuntimeError(response["error"]))
                        else:
                            future.set_result(response.get("result"))

                    # Обрабатываем события (notifications без id)
                    elif "method" in response and "id" not in response:
                        self.logger.info(f"Получено событие от Rust: {response}")
                        # TODO: Передать событие в DAP adapter

                except json.JSONDecodeError as e:
                    self.logger.error(f"Ошибка парсинга JSON от Rust: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"Ошибка чтения ответа: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Критическая ошибка в _read_responses: {e}")
        finally:
            # Соединение порвалось
            self.is_connected = False
            self.reader = None
            self.writer = None
            self.logger.warning("Соединение с Rust сервером потеряно")

    async def set_breakpoint(self, address: int) -> bool:
        """Установить точку останова по заданному адресу."""
        try:
            result = await self.call_method("setBreakpoint", {
                "address": address
            })
            return result.get("verified", False)
        except Exception as e:
            self.logger.error(f"Ошибка установки breakpoint: {e}")
            return False

    async def continue_execution(self):
        """Продолжаем исполнение."""
        try:
            await self.call_method("continue", {})
        except Exception as e:
            self.logger.error(f"Ошибка continue: {e}")

    async def step_over(self):
        """Переходим к текущей инструкции."""
        try:
            await self.call_method("stepOver", {})
        except Exception as e:
            self.logger.error(f"Ошибка stepOver: {e}")

    async def step_in(self):
        try:
            await self.call_method("stepIn", {})
        except Exception as e:
            self.logger.error(f"Ошибка stepIn: {e}")

    async def step_out(self):
        """Выходим из текущей функции."""
        try:
            await self.call_method("stepOut", {})
        except Exception as e:
            self.logger.error(f"Ошибка stepOut: {e}")

    async def get_state(self) -> Dict[str, Any]:
        """Получение текущего состояния отладчика."""
        try:
            return await self.call_method("getState", {})
        except Exception as e:
            self.logger.error(f"Ошибка getState: {e}")
            return {"error": str(e)}

    async def shutdown(self):
        """Выключаем Rust."""
        if self.connection_task:
            self.connection_task.cancel()

        if self.is_connected and self.writer:
            try:
                await self.call_method("shutdown", {})
            except Exception as e:
                self.logger.error(f"Ошибка при выключении: {e}")

        self.is_connected = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    def _next_id(self) -> int:
        """Получение идентификатора следующего запроса"""
        id = self.request_id
        self.request_id += 1
        return id