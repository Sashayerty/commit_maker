# CLI-утилита, которая будет создавать сообщение для коммита на основе ИИ.
# noqa: F841

import argparse
import importlib
import os
import subprocess

import requests
import rich.console
import rich_argparse

# Константы
mistral_api_key = os.environ.get("MISTRAL_API_KEY")
console = rich.console.Console()

# Настройка вывода --help (это не хардкод, такой способ указан в оф.
# документации rich_argparse)
rich_argparse.RichHelpFormatter.styles = {
    "argparse.args": "cyan bold",
    "argparse.groups": "green bold",
    "argparse.metavar": "dark_cyan",
    "argparse.prog": "dark_green bold",
}


# Функции для цветного вывода
def bold(text: str) -> str:
    """Возвращает жирный текст

    Args:
        text (str): Текст

    Returns:
        str: Жирный текст
    """
    bold_start = "\033[1m"
    bold_end = "\033[0m"
    return f"{bold_start}{text}{bold_end}"


def colored(
    string: str,
    color: str,
    text_bold: bool = True,
) -> str:
    """Функция для 'окраски' строк для красивого вывода

    Args:
        string (str): Строка, которую нужно покрасить
        color (str): Цвет покраски ['red', 'yellow', 'green', 'magenta',\
            'blue', 'cyan', 'reset']
        text_bold (bool, optional): Жирный текст или нет. Defaults to True.

    Returns:
        str: Покрашенная строка

    Example:
        `print(colored(string='Success!', color='green'))` # Выводит 'Success!'
        зеленого цвета
    """
    COLOR_RED = "\033[31m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BLUE = "\033[94m"
    COLOR_MAGENTA = "\033[95m"
    COLOR_CYAN = "\033[96m"
    COLOR_RESET = "\033[0m"
    COLORS_DICT = {
        "red": COLOR_RED,
        "green": COLOR_GREEN,
        "yellow": COLOR_YELLOW,
        "blue": COLOR_BLUE,
        "magenta": COLOR_MAGENTA,
        "cyan": COLOR_CYAN,
        "reset": COLOR_RESET,
    }
    return (
        bold(f"{COLORS_DICT[color]}{string}{COLORS_DICT['reset']}")
        if text_bold
        else f"{COLORS_DICT[color]}{string}{COLORS_DICT['reset']}"
    )


# Парсер параметров
parser = argparse.ArgumentParser(
    prog="commit_maker",
    description="CLI-утилита, которая будет создавать сообщение "
    "для коммита на основе ИИ. Можно использовать локальные модели/Mistral AI "
    "API. Локальные модели используют ollama.",
    formatter_class=rich_argparse.RichHelpFormatter,
)

# Общие параметры
general_params = parser.add_argument_group("Общие параметры")
general_params.add_argument(
    "-l",
    "--local-models",
    action="store_true",
    default=False,
    help="Запуск с использованием локальных моделей",
)
general_params.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    default=False,
    help="Запуск с выводом сообщения на основе зайстейдженных "
    "изменений, без создания коммита",
)
general_params.add_argument(
    "-V",
    "--version",
    action="version",
    version=f"%(prog)s {importlib.metadata.version('commit-maker')}",
)

# Параметры генерации
generation_params = parser.add_argument_group("Параметры генерации")
generation_params.add_argument(
    "-t",
    "--temperature",
    default=1.0,
    type=float,
    help="Температура модели при создании месседжа.\
        Находится на отрезке [0.0, 1.5]. Defaults to 1.0",
)
generation_params.add_argument(
    "-m",
    "--max-symbols",
    type=int,
    default=200,
    help="Длина сообщения коммита. Defaults to 200",
)
generation_params.add_argument(
    "-M",
    "--model",
    type=str,
    help="Модель, которую ollama будет использовать.",
)
generation_params.add_argument(
    "-e",
    "--exclude",
    nargs="+",
    help="Файлы, которые нужно игнорировать при создании сообщения коммита",
)


# Класс для использования API Mistral AI
class MistralAI:
    """Класс для общения с MistralAI.
    Написан с помощью requests."""

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
            "model": "mistral-small-latest",
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
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            print(colored(f"Ошибка при обращении к Mistral AI: {e}", "red"))
        except KeyError:
            print(colored("Ошибка парсинга ответа от Mistral AI", "red"))


# Класс для использования API Ollama
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
        data = {
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

        try:
            response = requests.post(
                url=self.url,
                json=data,
                headers=self.headers,
                timeout=60,
            )
            response.raise_for_status()  # выбросит ошибку при плохом статусе
            return response.json()["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            print(colored(f"Ошибка при обращении к Ollama: {e}", "red"))
        except KeyError:
            print(colored("Ошибка парсинга ответа от Ollama", "red"))


# main функция


def main() -> None:
    # Парсинг аргументов
    parsed_args = parser.parse_args()
    use_local_models = parsed_args.local_models
    max_symbols = parsed_args.max_symbols
    model = parsed_args.model
    dry_run = parsed_args.dry_run
    temperature = parsed_args.temperature
    excluded_files = parsed_args.exclude

    # Промпт для ИИ
    prompt_for_ai = f"""Привет! Ты составитель коммитов для git.
    Сгенерируй коммит-месседж на РУССКОМ языке, который:
    1. Точно отражает суть изменений
    2. Не превышает {max_symbols} символов
    Опирайся на данные от 'git status' и 'git diff'.
    В ответ на это сообщение тебе нужно предоставить
    ТОЛЬКО коммит. Пиши просто обычный текст, без markdown!"""

    try:
        if not use_local_models and not mistral_api_key:
            print(
                colored("Не найден MISTRAL_API_KEY для работы с API!", "red")
            )
            return

        # Получаем версию git, если он есть
        git_version = subprocess.run(  # noqa
            ["git", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout

        if use_local_models:
            # Получаем список моделей из Ollama, если Ollama есть
            ollama_list_of_models = (
                subprocess.run(
                    ["ollama", "ls"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                .stdout.strip()
                .split("\n")
            )
            ollama_list_of_models = [
                i.split()[0] for i in ollama_list_of_models[1:]
            ]
        else:
            ollama_list_of_models = 0

        # Обработка отсутствия ollama
        if not ollama_list_of_models and use_local_models:
            print(
                colored(
                    "Ollama не установлена или список моделей пуст!", "yellow"
                )
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
                                f"{i + 1}. {colored(model, 'magenta', False,)}"
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
                encoding="utf-8",
            )

            new_files = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            git_diff = subprocess.run(
                ["git", "diff", "--staged"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if (
                (not new_files.stdout)
                and (not git_diff.stdout)
                and (
                    not subprocess.run(
                        ["git", "diff"],
                        capture_output=True,
                        encoding="utf-8",
                    ).stdout
                )
            ):  # Проверка на отсутствие каких-либо изменений
                print(colored("Нет добавленных изменений!", "red"))
                return None
            if not git_diff.stdout:
                if not dry_run:
                    if (
                        input(
                            colored("Нет застейдженных изменений!", "red")
                            + " Добавить всё автоматически с помощью "
                            + colored("git add -A", "yellow")
                            + "? [y/N]: "
                        )
                        == "y"
                    ):
                        subprocess.run(
                            ["git", "add", "-A"],
                        )
                    else:
                        print(
                            colored(
                                "Добавьте необходимые файлы вручную.", "yellow"
                            )
                        )
                        return None
                else:
                    print(
                        colored("Нечего коммитить!", "red")
                        + " Добавьте необходимые файлы с помощью "
                        + colored("git add <filename>", "yellow")
                    )
                    return None
                git_diff = subprocess.run(
                    ["git", "diff", "--staged"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
            if subprocess.run(
                ["git", "diff"],
                capture_output=True,
                encoding="utf-8",
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
                    + colored("git add <filename>", "yellow")
                    + "."
                )
            if use_local_models:
                client = Ollama(model=model)
            else:
                client = MistralAI(
                    api_key=mistral_api_key,
                )
            if not dry_run:
                retry = True
                while retry:
                    with console.status(
                        "[magenta bold]Создание сообщения коммита...",
                        spinner_style="magenta",
                    ):
                        commit_message = client.message(
                            message=prompt_for_ai
                            + "Git status: "
                            + git_status.stdout
                            + "Git diff: "
                            + git_diff.stdout,
                            temperature=temperature,
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
                    subprocess.run(
                        ["git", "commit", "-m", f"{commit_message}"],
                        encoding="utf-8",
                    )
                    print(colored("Коммит успешно создан!", "green"))
            else:
                commit_message = client.message(
                    message=prompt_for_ai
                    + "Git status: "
                    + git_status.stdout
                    + "Git diff: "
                    + git_diff.stdout,
                    temperature=temperature,
                )
                print(
                    colored(
                        "Коммит-месседж успешно сгенерирован:", "green", False
                    )
                )
                print(
                    colored(
                        commit_message,
                        "yellow",
                        False,
                    )
                )
                return None

        # Если нет
        else:
            init_git_repo = (
                True
                if input(
                    colored("Не инициализирован git репозиторий!", "red")
                    + " Выполнить "
                    + colored("git init", "yellow")
                    + "? [y/N]: "
                )
                == "y"
                else False
            )
            if init_git_repo:
                subprocess.run(
                    ["git", "init"],
                    capture_output=True,
                    encoding="utf-8",
                )

                (
                    (
                        subprocess.run(
                            ["git", "add", "-A"],
                        ),
                        subprocess.run(
                            [
                                "git",
                                "commit",
                                "-m",
                                "'Initial commit'",
                            ],
                            encoding="utf-8",
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
    except FileNotFoundError as e:
        print(
            colored("Ollama не установлена!", "red")
            if "ollama" in str(e)
            else colored(str(e), "red")
        )
    except Exception as e:
        print(colored("Ошибка:", "red") + " " + str(e))


if __name__ == "__main__":
    main()
