# CLI-утилита, которая будет создавать сообщение для коммита на основе ИИ.
# noqa: F841

import argparse
import json
import os
import subprocess
import urllib
import urllib.request

# Константы

mistral_api_key = os.environ["MISTRAL_API_KEY"]
# Для цветных логов
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"
# Парсер параметров
parser = argparse.ArgumentParser(
    prog="Commit Maker",
    usage="commit_maker [OPTION] [VALUE]",
    description="CLI-утилита, которая будет создавать сообщение"
    "для коммита на основе ИИ.",
)
parser.add_argument(
    "--local-models",
    "-l",
    action="store_true",
    default=False,
    help="Использовать локальные модели или нет",
)
parser.add_argument(
    "--max-symbols",
    "-m",
    type=int,
    default=150,
    metavar="[max_symbols]",
    help="Длина сообщения коммита. Defaults to 150",
)
# Парсинг аргументов
use_local_models = parser.parse_args().local_models
max_symbols = parser.parse_args().max_symbols


# Промпт для ИИ
prompt_for_ai = f"""Привет! Ты составитель коммитов для git.
Сгенерируй коммит-месседж на русском языке, который:
1. Точно отражает суть изменений
2. Не превышает {max_symbols} символов
Опирайся на данные от 'git status' и 'git diff'.
В ответ на это сообщение тебе нужно предоставить
ТОЛЬКО коммит. Пиши просто обычный текст, без markdown!"""


# Класс для использования API Mistral AI
class MistralAI:
    """Класс для общения с MistralAI. Написан с помощью urllib."""

    def __init__(self, api_key: str):
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
        self.data = {
            "model": "mistral-small-latest",
            "messages": [],
            "temperature": 0.7,
        }

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
        self.data["messages"] = [
            {
                "role": role,
                "content": message,
            }
        ]
        post_data = json.dumps(self.data).encode("utf-8")
        request = urllib.request.Request(
            url=self.url,
            data=post_data,
            headers=self.headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    response_data = json.loads(response.read().decode())
                    return response_data["choices"][0]["message"]["content"]
                else:
                    print(f"Ошибка: {response.status}")
        except urllib.error.URLError as e:
            print(f"Ошибка URL: {e.reason}")
        except urllib.error.HTTPError as e:
            print(f"Ошибка HTTP: {e.code} {e.reason}")
            print(f"Ответ сервера: {e.read().decode()}")


# Класс для использования API Ollama
class Ollama:
    """Класс для общения с локальными моделями Ollama.
    Написан с помощью urllib."""

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
        message: str,
        temperature: float = 0.7,
        role: str = "user",
    ) -> str:
        """Функция сообщения

        Args:
            message (str): Сообщение
            model (str): Модель, с которой будем общаться
            temperature (float, optional): Температура общения. Defaults to 0.7
            role (str, optional): Роль в сообщении.

        Returns:
            str: Json-ответ/Err
        """
        self.data = {
            "model": self.model,
            "messages": [
                {
                    "role": role,
                    "content": message,
                }
            ],
            "options": {
                "temperature": temperature,
            },
            "stream": False,
        }
        post_data = json.dumps(self.data).encode("utf-8")
        request = urllib.request.Request(
            url=self.url,
            data=post_data,
            headers=self.headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    response_data = json.loads(response.read().decode())
                    return response_data["message"]["content"]
                else:
                    print(f"Ошибка: {response.status}")
        except urllib.error.URLError as e:
            print(f"Ошибка URL: {e.reason}")
        except urllib.error.HTTPError as e:
            print(f"Ошибка HTTP: {e.code} {e.reason}")
            print(f"Ответ сервера: {e.read().decode()}")


# main функция


def main() -> None:
    global mistral_api_key, prompt_for_ai, use_local_models
    try:
        # Получаем версию git, если он есть
        git_version = subprocess.run(  # noqa
            ["git", "--version"],
            capture_output=True,
        ).stdout.decode()

        # Получаем версию Ollama, если есть
        ollama_version = subprocess.run(
            ["ollama", "-v"],
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Обработка отсутствия ollama
        if not ollama_version and use_local_models:
            print(
                f"{COLOR_YELLOW}Ollama не установлена!{COLOR_RESET} "
                "Для установки перейдите по https://ollama.com/download"
            )
            return None

        # Проверяем, есть ли .git
        dot_git = ".git" in os.listdir("./")

        # Если есть
        if dot_git:
            # Получаем разницу в коммитах
            git_status = subprocess.run(
                ["git", "status", "-v"],
                capture_output=True,
            )

            new_files = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
            )

            git_diff = subprocess.run(
                ["git", "diff", "--staged"],
                capture_output=True,
            )
            if (
                (not new_files.stdout)
                and (not git_diff.stdout)
                and (
                    not subprocess.run(
                        ["git", "diff"],
                        capture_output=True,
                    ).stdout
                )
            ):  # Проверка на отсутствие каких-либо изменений
                print(f"{COLOR_RED}Нет добавленных изменений!{COLOR_RESET}")
                return None
            if not git_diff.stdout:
                if (
                    input(
                        f"{COLOR_RED}Нет застейдженных изменений!"
                        f"{COLOR_RESET} Добавить всё автоматически "
                        f"с помощью {COLOR_YELLOW}'git add -A'{COLOR_RESET}? "
                        "[y/N]: "
                    )
                    == "y"
                ):
                    subprocess.run(
                        ["git", "add", "-A"],
                        capture_output=True,
                    )
                else:
                    print(
                        f"{COLOR_YELLOW}Добавьте необходимые "
                        f"файлы вручную.{COLOR_RESET}"
                    )
                    return None
                git_diff = subprocess.run(
                    ["git", "diff", "--staged"],
                    capture_output=True,
                )
            if subprocess.run(
                ["git", "diff"],
                capture_output=True,
            ).stdout:
                print(
                    f"{COLOR_RED}Обратите внимание, что у Вас есть "
                    f"незастейдженные изменения!{COLOR_RESET} Для добавления "
                    f"дополнительных файлов {COLOR_YELLOW}Ctrl + "
                    f"C{COLOR_RESET} и выполните {COLOR_YELLOW}'git add "
                    f"<filename>'{COLOR_RESET}."
                )
            if use_local_models:
                client = Ollama(model="gemma3:12b")
            else:
                client = MistralAI(
                    api_key=mistral_api_key,
                )
            retry = True
            while retry:
                commit_message = client.message(
                    message=prompt_for_ai
                    + "Git status: "
                    + git_status.stdout.decode()
                    + "Git diff: "
                    + git_diff.stdout.decode(),
                    temperature=1.0,
                )
                commit_with_message_from_ai = input(
                    "Закоммитить с сообщением "
                    f"{COLOR_YELLOW}'{commit_message}'{COLOR_RESET}? [y/N/r]: "
                )
                if commit_with_message_from_ai != "r":
                    retry = False
                    break
            if commit_with_message_from_ai == "y":
                subprocess.run(["git", "commit", "-m", f"{commit_message}"])
                print(f"{COLOR_GREEN}Коммит успешно создан!{COLOR_RESET}")

        # Если нет
        else:
            init_git_repo = (
                True
                if input(
                    "Не инициализирован git репозиторий! "
                    f"Выполнить {COLOR_YELLOW}'git init'{COLOR_RESET}? [y/N]: "
                )
                == "y"
                else False
            )
            if init_git_repo:
                subprocess.run(
                    ["git", "init"],
                    capture_output=True,
                )

                (
                    (
                        subprocess.run(
                            ["git", "add", "-A"],
                            capture_output=True,
                        ),
                        subprocess.run(
                            [
                                "git",
                                "commit",
                                "-m",
                                "'Initial commit'",
                            ]
                        ),
                    )
                    if input(
                        "Сделать первый коммит с сообщением "
                        f"{COLOR_YELLOW}'Initial commit?'{COLOR_RESET} [y/N]: "
                    )
                    == "y"
                    else None
                )
    except Exception as e:
        print(f"{COLOR_RED}Ошибка:{COLOR_RESET} {e}")


if __name__ == "__main__":
    main()
