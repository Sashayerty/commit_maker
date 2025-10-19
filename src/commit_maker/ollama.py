# Класс для использования API Ollama
from typing import Optional

import requests
import rich.console

console = rich.console.Console()


class Ollama:
    """Класс для общения с локальными моделями Ollama.
    Написан с помощью requests."""

    def __init__(
        self,
        model: str,
    ):
        """Инициализация класса"""
        self.model = model
        self.url = "http://localhost:11434/api/chat"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def message(
        self,
        messages: list[dict[str]],
        timeout: Optional[int],
        temperature: float,
    ) -> str:
        """Функция сообщения

        Args:
            messages (list[dict[str]]): Список сообщений
            timeout (int): Таймаут ожидания сообщения
            model (str): Модель, с которой будем общаться
            temperature (float, optional): Температура общения. Defaults to 0.7

        Returns:
            str: Json-ответ/Err
        """
        data = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": temperature,
            },
            "stream": False,
        }

        try:
            response = requests.post(
                url=self.url,
                json=data,
                headers=self.headers,
                timeout=timeout,
            )
            response.raise_for_status()  # выбросит ошибку при плохом статусе
            return response.json()["message"]["content"]

        except requests.exceptions.RequestException:
            console.print_exception()
        except KeyError:
            console.print_exception()
