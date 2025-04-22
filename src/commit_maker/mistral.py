# Класс для использования API Mistral AI
import requests
import rich.console

console = rich.console.Console()


class MistralAI:
    """Класс для общения с MistralAI.
    Написан с помощью requests."""

    def __init__(
        self,
        api_key: str,
        model: str = "mistral-small-latest",
    ):
        """Инициализация класса

        Args:
            api_key (str): Апи ключ MistralAI
        """
        self.url = "https://api.mistral.ai/v1/chat/completions"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        self.model = model

    def message(
        self,
        message: str,
        role: str = "user",
        temperature: float = 0.7,
    ) -> str:
        """Функция сообщения

        Args:
            message (str): Сообщение
            role (str, optional): Роль. Defaults to "user".

        Returns:
            str: Json-ответ/Err
        """
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": role,
                    "content": message,
                }
            ],
            "temperature": 0.7,
        }
        try:
            response = requests.post(
                url=self.url,
                json=data,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException:
            console.print_exception()
        except KeyError:
            console.print_exception()
