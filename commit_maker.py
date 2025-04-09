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
COLORS_DICT = {
    "red": COLOR_RED,
    "green": COLOR_GREEN,
    "yellow": COLOR_YELLOW,
    "reset": COLOR_RESET,
}

# Парсер параметров
parser = argparse.ArgumentParser(
    prog="Commit Maker",
    usage="commit_maker [OPTION] [VALUE]",
    description="CLI-утилита, которая будет создавать сообщение "
    "для коммита на основе ИИ. Можно использовать локальные модели/Mistral AI "
    "API. Локальные модели используют ollama.",
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
    default=250,
    metavar="[max_symbols]",
    help="Длина сообщения коммита. Defaults to 150",
)
parser.add_argument(
    "--model",
    "-M",
    type=str,
    metavar="[model]",
    help="Модель, которую ollama будет использовать.",
)
parser.add_argument(
    "--dry-run",
    "-d",
    action="store_true",
    default=False,
    help="Запуск с выводом сообщения, без создания коммита",
)

# Парсинг аргументов
use_local_models = parser.parse_args().local_models
max_symbols = parser.parse_args().max_symbols
model = parser.parse_args().model
dry_run = parser.parse_args().dry_run

# Промпт для ИИ
prompt_for_ai = f"""Привет! Ты составитель коммитов для git.
Сгенерируй коммит-месседж на РУССКОМ языке, который:
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
                    print(response.read())
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


def colored(string: str, color: str) -> str:
    global COLORS_DICT
    return f"{COLORS_DICT[color]}{string}{COLORS_DICT["reset"]}"


# main функция


def main() -> None:
    global mistral_api_key, prompt_for_ai, use_local_models, model
    try:
        # Получаем версию git, если он есть
        git_version = subprocess.run(  # noqa
            ["git", "--version"],
            capture_output=True,
            text=True,
        ).stdout

        # Получаем версию Ollama, если есть
        ollama_list_of_models = (
            subprocess.run(
                ["ollama", "ls"],
                capture_output=True,
                text=True,
            )
            .stdout.strip()
            .split("\n")
        )

        # Обработка отсутствия ollama
        if not ollama_list_of_models and use_local_models:
            print(
                colored("Ollama не установлена!", "yellow")
                + " Для установки перейдите по https://ollama.com/download"
            )
            return None
        elif not use_local_models and model:
            print(
                f"Для использования {model} локально используйте флаг "
                + colored("--local-models", "yellow")
                + ". Если нужна помощь: "
                + colored("--help", "yellow")
            )
            return None
        elif ollama_list_of_models and use_local_models:
            ollama_list_of_models = [
                i.split()[0] for i in ollama_list_of_models[1:]
            ]
            if not model:
                if len(ollama_list_of_models) > 1:
                    print(
                        colored(
                            "Для использования локальных моделей необходимо "
                            "выбрать модель:",
                            "yellow",
                        )
                        + "\n"
                        + "\n".join(
                            [
                                f"{i + 1}. {model}"
                                for i, model in enumerate(
                                    ollama_list_of_models
                                )
                            ]
                        )
                    )
                    model_is_selected = False
                    while not model_is_selected:
                        model = input(
                            colored(
                                "Введите число от 1 до "
                                f"{len(ollama_list_of_models)}: ",
                                "yellow",
                            )
                        )
                        model = int(model) if model.isdigit() else -1
                        if model > len(ollama_list_of_models) or model == -1:
                            continue
                        model = ollama_list_of_models[model - 1]
                        model_is_selected = True
                        break
                else:
                    model = ollama_list_of_models[0]
            else:
                if model not in ollama_list_of_models:
                    print(
                        colored(
                            f"{model} не является доступной моделью! ", "red"
                        )
                        + "Доступные модели: "
                        + colored(
                            f"{', '.join(ollama_list_of_models)}", "yellow"
                        )
                    )
                    return None
        if model:
            print("Выбрана модель: " + colored(model, "yellow"))

        # Проверяем, есть ли .git
        dot_git = ".git" in os.listdir("./")

        # Если есть
        if dot_git:
            # Получаем разницу в коммитах
            git_status = subprocess.run(
                ["git", "status", "-v"],
                capture_output=True,
                text=True,
            )

            new_files = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
            )

            git_diff = subprocess.run(
                ["git", "diff", "--staged"],
                capture_output=True,
                text=True,
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
                print(colored("Нет добавленных изменений!", "red"))
                return None
            if not git_diff.stdout:
                if (
                    input(
                        colored("Нет застейдженных изменений!", "red")
                        + " Добавить всё автоматически с помощью "
                        + colored("'git add -A'", "yellow")
                        + "? [y/N]: "
                    )
                    == "y"
                ):
                    subprocess.run(
                        ["git", "add", "-A"],
                        capture_output=True,
                    )
                else:
                    print(
                        colored(
                            "Добавьте необходимые файлы вручную.", "yellow"
                        )
                    )
                    return None
                git_diff = subprocess.run(
                    ["git", "diff", "--staged"],
                    capture_output=True,
                    text=True,
                )
            if subprocess.run(
                ["git", "diff"],
                capture_output=True,
            ).stdout:
                print(
                    colored(
                        "Обратите внимание на то, что у Вас "
                        "есть незастейдженные изменения!",
                        "red",
                    )
                    + " Для добавления дополнительных файлов "
                    + colored("Ctrl + C", "yellow")
                    + " и выполните "
                    + colored("'git add <filename>'", "yellow")
                    + "."
                )
            if use_local_models:
                client = Ollama(model=model)
            else:
                client = MistralAI(
                    api_key=mistral_api_key,
                )
            retry = True
            while retry:
                commit_message = client.message(
                    message=prompt_for_ai
                    + "Git status: "
                    + git_status.stdout
                    + "Git diff: "
                    + git_diff.stdout,
                    temperature=1.0,
                )
                commit_with_message_from_ai = input(
                    "Закоммитить с сообщением "
                    + colored(f"'{commit_message}'", "yellow")
                    + "? [y/N/r]: "
                )
                if commit_with_message_from_ai != "r":
                    retry = False
                    break
            if commit_with_message_from_ai == "y":
                subprocess.run(["git", "commit", "-m", f"{commit_message}"])
                print(colored("Коммит успешно создан!", "green"))

        # Если нет
        else:
            init_git_repo = (
                True
                if input(
                    "Не инициализирован git репозиторий! Выполнить "
                    + colored("'git init'", "yellow")
                    + "? [y/N]: "
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
                        + colored("'Initial commit?'", "yellow")
                        + " [y/N]: "
                    )
                    == "y"
                    else None
                )
    except Exception as e:
        print(colored("Ошибка:", "red") + " " + str(e))


if __name__ == "__main__":
    main()
