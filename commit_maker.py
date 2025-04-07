# CLI-утилита, которая будет создавать сообщение для коммита на основе ИИ.

import json
import os
import subprocess
import urllib
import urllib.request

# Константы

mistral_api_key = os.environ["MISTRAL_API_KEY"]
prompt = """Привет! Ты составитель коммитов для git. Твоя задача, опираясь на
данные от 'git status' и 'git diff' написать короткий и ёмкий коммит. В ответ
на это сообщение тебе нужно предоставить ТОЛЬКО коммит. Пиши просто обычный
текст, без markdown!"""

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
        }

    def message(self, message: str, role: str = "user") -> str:
        """Функция сообщения

        Args:
            message (str): Сообщение
            role (str, optional): Роль. Defaults to "user".

        Returns:
            str: Json-ответ/Err
        """
        self.data["messages"].append(
            {
                "role": role,
                "content": message,
            }
        )
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


# client = MistralAI(api_key=mistral_api_key)
# print((client.message(message=prompt + "Git status:" + "" + "Git diff" + ""))

# main функция


def main() -> None:
    global mistral_api_key, prompt
    try:
        # Получаем версию git, если он есть
        git_version = subprocess.run(  # noqa
            ["git", "--version"],
            capture_output=True,
        ).stdout.decode()

        # Проверяем, есть ли .git

        dot_git = ".git" in os.listdir("./")

        # Если есть
        if dot_git:
            # Получаем разницу в коммитах
            git_status = subprocess.run(
                ["git", "status", "-v"],
                capture_output=True,
            )
            git_diff = subprocess.run(
                ["git", "diff"],
                capture_output=True,
            )
            if not git_status.stdout and not git_diff.stdout:
                print("Нет добавленных изменений!")
                return None
            # print(git_status.stdout.decode())
            # print(git_diff.stdout.decode())
            client = MistralAI(
                api_key=mistral_api_key,
            )
            retry = True
            while retry:
                commit_message = client.message(
                    message=prompt
                    + "Git status: "
                    + git_status.stdout.decode()
                    + "Git diff: "
                    + git_diff.stdout.decode()
                )
                commit_with_message_from_ai = input(
                    "Закоммитить с сообщением "
                    f"'{commit_message}'? [y/N/retry]: "
                )
                if commit_with_message_from_ai != "retry":
                    retry = False
                    break
            if commit_with_message_from_ai == "y":
                subprocess.run(
                    ["git", "add", "-A"],
                    capture_output=True,
                )
                subprocess.run(["git", "commit", "-m", f"{commit_message}"])

        # Если нет
        else:
            init_git_repo = (
                True
                if input(
                    "Не инициализирован git репозиторий! "
                    "Выполнить 'git init'? [y/N]: "
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
                        "'Initial commit?' [y/N]: "
                    )
                    == "y"
                    else None
                )
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
