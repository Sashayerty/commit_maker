# CLI-утилита, которая будет создавать сообщение для коммита на основе ИИ.
import argparse
import importlib
import os
import subprocess

import requests
import rich.console
import rich.prompt

from .colored import colored
from .custom_int_prompt import CustomIntPrompt
from .mistral import MistralAI
from .ollama import Ollama
from .rich_custom_formatter import CustomFormatter

# Константы
mistral_api_key = os.environ.get("MISTRAL_API_KEY")
console = rich.console.Console()
prompt = CustomIntPrompt()

# Парсер параметров
parser = argparse.ArgumentParser(
    prog="commit_maker",
    description="CLI-утилита, которая будет создавать сообщение "
    "для коммита на основе ИИ. Можно использовать локальные модели/Mistral AI "
    "API. Локальные модели используют ollama.",
    formatter_class=CustomFormatter,
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
    default=[],
    help="Файлы, которые нужно игнорировать при создании сообщения коммита",
)
general_params.add_argument(
    "-w",
    "--wish",
    default=None,
    type=str,
    help="Пожелания/правки для сообщения.",
)


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
    wish = parsed_args.wish

    # Промпт для ИИ
    prompt_for_ai = f"""Привет! Ты составитель коммитов для git.
    Сгенерируй коммит-месседж на РУССКОМ языке, который:
    1. Точно отражает суть изменений
    2. Не превышает {max_symbols} символов
    Опирайся на данные от 'git status' и 'git diff'.
    Учти пожелания пользователя: {wish}.
    В ответ на это сообщение тебе нужно предоставить
    ТОЛЬКО коммит. Пиши просто обычный текст, без markdown!"""

    try:
        if not use_local_models and not mistral_api_key:
            console.print(
                "Не найден MISTRAL_API_KEY для работы с API!",
                style="red",
                highlight=False,
            )
            return

        # Получаем версию git, если он есть
        git_version = subprocess.run(  # noqa
            ["git", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout

        # Проверяем, есть ли .git
        dot_git = ".git" in os.listdir("./")

        # Если есть
        if dot_git:
            # Получаем разницу в коммитах
            git_status = subprocess.run(
                ["git", "status"],
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

            if excluded_files:
                git_diff_command = ["git", "diff", "--staged", "--", "."]
                git_diff_command.extend(
                    [f":!{file}" for file in excluded_files]
                )
            else:
                git_diff_command = ["git", "diff", "--staged"]

            git_diff = subprocess.run(
                git_diff_command,
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
                console.print(
                    "[red]Нет добавленных изменений![/red]",
                    highlight=False,
                )
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
                        console.print(
                            "Добавьте необходимые файлы вручную.",
                            style="yellow",
                            highlight=False,
                        )
                        return None
                else:
                    console.print(
                        "[red]Нечего коммитить![/red]"
                        " Добавьте необходимые файлы с помощью "
                        "[yellow]git add <filename>[/yellow]",
                        highlight=False,
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
                console.print(
                    "[red]Обратите внимание на то, что у Вас "
                    "есть незастейдженные изменения![/red]"
                    " Для добавления дополнительных файлов "
                    "[yellow]Ctrl + C[/yellow] и выполните "
                    "[yellow]git add <filename>[/yellow]",
                    highlight=False,
                )

            if use_local_models:

                # Смотрим на установку Ollama
                try:
                    subprocess.run(
                        ["ollama", "--version"],
                        text=True,
                        capture_output=True,
                    )
                except FileNotFoundError:
                    console.print(
                        "Ollama не установлена!",
                        style="red bold",
                    )
                    return None

                # Проверка на запущенную Ollama
                ollama_served = (
                    requests.get("http://localhost:11434").status_code == 200
                )

                if ollama_served:
                    # Получаем список моделей из Ollama
                    ollama_models_json = requests.get(
                        "http://localhost:11434/api/tags"
                    ).json()
                    if ollama_models_json["models"]:
                        ollama_list_of_models = [
                            i["model"] for i in ollama_models_json["models"]
                        ]
                    else:
                        console.print(
                            "[yellow]Список моделей Ollama пуст!"
                            "[/yellow] Для установки перейдите по "
                            "https://ollama.com/models",
                            highlight=False,
                        )
                        return None
                else:
                    console.print(
                        "[yellow]Сервер Ollama не запущен или Ollama не "
                        "установлена![/yellow]"
                    )
                    return None
            else:
                ollama_list_of_models = 0

            # Обработка отсутствия ollama
            if not ollama_list_of_models and use_local_models:
                console.print(
                    "[yellow]Ollama не установлена или список моделей пуст!"
                    "[/yellow] Для установки перейдите по "
                    "https://ollama.com/download",
                    highlight=False,
                )
                return None
            elif not use_local_models and model:
                console.print(
                    f"Для использования {model} локально используйте флаг "
                    "[yellow]--local-models[/yellow]. Если нужна помощь: "
                    "[yellow]--help[/yellow]",
                    highlight=False,
                )
                return None
            elif ollama_list_of_models and use_local_models:
                if not model:
                    if len(ollama_list_of_models) > 1:
                        console.print(
                            "[yellow]Для использования локальных моделей "
                            "необходимо "
                            "выбрать модель:[/yellow]\n"
                            + "\n".join(
                                [
                                    f"[magenta]{i + 1}. {model}[/magenta]"
                                    for i, model in enumerate(
                                        ollama_list_of_models
                                    )
                                ]
                            ),
                            highlight=False,
                        )
                        model_is_selected = False
                        while not model_is_selected:
                            model = prompt.ask(
                                "[yellow]Введите число от 1 до "
                                f"{len(ollama_list_of_models)}: [/yellow]",
                            )
                            if not 1 <= model <= len(ollama_list_of_models):
                                console.print(
                                    "[red]Введите корректное число![/red]",
                                    highlight=False,
                                )
                                continue
                            model = ollama_list_of_models[model - 1]
                            model_is_selected = True
                            break
                    else:
                        model = ollama_list_of_models[0]
                else:
                    if model not in ollama_list_of_models:
                        console.print(
                            f"[red]{model} не является доступной моделью!"
                            "[/red] "
                            "Доступные модели: [yellow]"
                            f"{', '.join(ollama_list_of_models)}[/yellow]",
                            highlight=False,
                        )
                        return None
            if model:
                console.print(
                    f"Выбрана модель: [yellow]{model}[/yellow]",
                    highlight=False,
                )
            # Создание клиента для общения с ИИ
            if use_local_models:
                client = Ollama(model=model)
            else:
                client = MistralAI(
                    api_key=mistral_api_key,
                    model="mistral-large-latest",
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
                    console.print(
                        "Коммит успешно создан!",
                        style="green bold",
                        highlight=False,
                    )
            else:
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
                console.print(commit_message, style="yellow", highlight=False)
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
    except KeyboardInterrupt:
        return None
    except Exception:
        console.print_exception()


if __name__ == "__main__":
    main()
