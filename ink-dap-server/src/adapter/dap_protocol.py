"""
Реализация протокола отладочного адаптера (DAP)
Обрабатывает низкоуровневое чтение и запись сообщений DAP
"""

import json
import sys
from typing import Dict, Any, Optional
import logging


class DAPProtocol:
    """Занимается кодированием/декодированием сообщений DAP через stdin/stdout."""

    def __init__(self):
        self.logger = logging.getLogger("InkDebugAdapter.DAPProtocol")
        self._sequence = 1

    def read_message(self) -> Optional[Dict[str, Any]]:
        """
        Чтение DAP-сообщения из stdin.

        Формат сообщений DAP:
        Content-Length: <length>\r\n
         \r\n
         <json-content>.
        """
        try:
            # Чтение заголовков
            headers = {}
            while True:
                line = sys.stdin.readline()
                if not line:
                    return None

                line = line.strip()
                if not line:  # Пустая строка - отмечает конец заголовков
                    break

                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

            # Получить длину содержимого
            content_length = int(headers.get("Content-Length", 0))
            if content_length == 0:
                self.logger.error("Заголовок Content-Length не найден")
                return None

            # body
            body = sys.stdin.read(content_length)
            if not body:
                return None

            # Парс JSON
            message = json.loads(body)
            self.logger.debug(f"Получено: {message}")
            return message

        except Exception as e:
            self.logger.error(f"Сообщение об ошибке: {e}")
            return None

    def send_message(self, message: Dict[str, Any]):
        """Отправка сообщения DAP в stdout."""
        try:
            # Convert to JSON
            body = json.dumps(message)

            # Отправка заголовков и тела
            content_length = len(body.encode('utf-8'))
            sys.stdout.write(f"Content-Length: {content_length}\r\n\r\n")
            sys.stdout.write(body)
            sys.stdout.flush()

            self.logger.debug(f"Отправлено: {message}")

        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}")

    def send_response(self, request: Dict[str, Any], body: Optional[Dict[str, Any]] = None, success: bool = True):
        """Отправка ответа на запрос DAP"""
        response = {
            "type": "response",
            "request_seq": request.get("seq", 0),
            "success": success,
            "command": request.get("command", ""),
            "seq": self._next_seq()
        }

        if body:
            response["body"] = body

        self.send_message(response)

    def send_event(self, event: str, body: Optional[Dict[str, Any]] = None):
        """Отправка события DAP."""
        message = {
            "type": "event",
            "event": event,
            "seq": self._next_seq()
        }

        if body:
            message["body"] = body

        self.send_message(message)

    def _next_seq(self) -> int:
        """Получение следующего порядкового номера."""
        seq = self._sequence
        self._sequence += 1
        return seq