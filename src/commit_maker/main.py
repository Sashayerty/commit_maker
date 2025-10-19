# CLI utility that generates commit messages using AI.
import argparse
import importlib
import os
import subprocess

import requests
import rich.console

from .colored import colored
from .custom_int_prompt import CustomIntPrompt
from .cut_think_part import cut_think
from .mistral import MistralAI
from .ollama import Ollama
from .rich_custom_formatter import CustomFormatter

# Constants
mistral_api_key = os.environ.get("MISTRAL_API_KEY")
console = rich.console.Console()
prompt = CustomIntPrompt()
available_langs = ["en", "ru"]

# Argument parser
parser = argparse.ArgumentParser(
    prog="commit_maker",
    description="CLI utility that generates commit messages using AI. "
    "Supports local models/Mistral AI API. Local models use ollama.",
    formatter_class=CustomFormatter,
)

# General parameters
general_params = parser.add_argument_group("General parameters")
general_params.add_argument(
    "-l",
    "--local-models",
    action="store_true",
    default=False,
    help="Use local models",
)
general_params.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    default=False,
    help="Dry run: show commit message without creating commit",
)
general_params.add_argument(
    "-V",
    "--version",
    action="version",
    version=f"%(prog)s {importlib.metadata.version('commit-maker')}",
)
general_params.add_argument(
    "-o",
    "--timeout",
    type=int,
    default=None,
    help="Change timeout for models. Default is None.",
)

# Generation parameters
generation_params = parser.add_argument_group("Generation parameters")
generation_params.add_argument(
    "-t",
    "--temperature",
    default=1.0,
    type=float,
    help="Model temperature for message generation. "
         "Range: [0.0, 1.5]. Default: 1.0",
)
generation_params.add_argument(
    "-m",
    "--max-symbols",
    type=int,
    default=200,
    help="Maximum commit message length. Default: 200",
)
generation_params.add_argument(
    "-M",
    "--model",
    type=str,
    help="Model to be used by ollama",
)
generation_params.add_argument(
    "-e",
    "--exclude",
    nargs="+",
    default=[],
    help="Files to exclude when generating commit message",
)
generation_params.add_argument(
    "-w",
    "--wish",
    default=None,
    type=str,
    help="Custom wishes/edits for the commit message",
)
generation_params.add_argument(
    "-L",
    "--language",
    choices=available_langs,
    default="ru",
    help="Language of generated commit message (en/ru)",
)


# Main function


def main() -> None:
    # Parsing arguments
    parsed_args = parser.parse_args()
    use_local_models = parsed_args.local_models
    max_symbols = parsed_args.max_symbols
    model = parsed_args.model
    dry_run = parsed_args.dry_run
    temperature = parsed_args.temperature
    excluded_files = parsed_args.exclude
    wish = parsed_args.wish
    timeout = parsed_args.timeout
    lang = parsed_args.language

    # AI prompt
    prompt_for_ai = f"""You are a git commit message generator.
    Generate a single commit message in
    {"Russian" if lang == "ru" else "English"} that:
    Clearly summarizes the purpose of the changes.
    Does not exceed {max_symbols} characters.
    Uses information from git status and git diff.
    Takes into account user preferences: {wish}.
    Output only the commit message — plain text, no markdown, no
    explanations, no formatting."""

    try:
        if not use_local_models and not mistral_api_key:
            console.print(
                "MISTRAL_API_KEY not found for API usage!",
                style="red",
                highlight=False,
            )
            return

        # Get git version if available
        git_version = subprocess.run(  # noqa
            ["git", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout

        # Check if .git exists
        dot_git = ".git" in os.listdir("./")

        # If .git exists
        if dot_git:
            # Get commit differences
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
                git_diff_command.extend([f":!{file}" for file in excluded_files])  # noqa
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
            ):  # Check for no changes
                console.print(
                    "[red]No changes added![/red]",
                    highlight=False,
                )
                return None
            if not git_diff.stdout:
                if not dry_run:
                    if (
                        input(
                            colored("No staged changes!", "red")
                            + " Add all automatically using "
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
                            "Add required files manually.",
                            style="yellow",
                            highlight=False,
                        )
                        return None
                else:
                    console.print(
                        "[red]Nothing to commit![/red]"
                        " Add required files using "
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
                    "[red]Note: You have unstaged changes![/red]"
                    " To add more files, press "
                    "[yellow]Ctrl + C[/yellow] and run "
                    "[yellow]git add <filename>[/yellow]",
                    highlight=False,
                )

            if use_local_models:
                # Check Ollama installation
                try:
                    subprocess.run(
                        ["ollama", "--version"],
                        text=True,
                        capture_output=True,
                    )
                except FileNotFoundError:
                    console.print(
                        "Ollama is not installed!",
                        style="red bold",
                    )
                    return None

                # Check if Ollama is running
                ollama_served = (
                    requests.get("http://localhost:11434").status_code == 200
                )

                if ollama_served:
                    # Get list of models from Ollama
                    ollama_models_json = requests.get(
                        "http://localhost:11434/api/tags"
                    ).json()
                    if ollama_models_json["models"]:
                        ollama_list_of_models = [
                            i["model"] for i in ollama_models_json["models"]
                        ]
                    else:
                        console.print(
                            "[yellow]Ollama model list is empty!"
                            "[/yellow] To install models, visit "
                            "https://ollama.com/models",
                            highlight=False,
                        )
                        return None
                else:
                    console.print(
                        "[yellow]Ollama server not running\n"
                        "or not installed![/yellow]"
                    )
                    return None
            else:
                ollama_list_of_models = 0

            # Handle missing Ollama
            if not ollama_list_of_models and use_local_models:
                console.print(
                    "[yellow]Ollama is not installed or model list is empty!"
                    "[/yellow] To install, visit "
                    "https://ollama.com/download",
                    highlight=False,
                )
                return None
            elif not use_local_models and model:
                console.print(
                    f"To use {model} locally, use the flag "
                    "[yellow]--local-models[/yellow]. For help: "
                    "[yellow]--help[/yellow]",
                    highlight=False,
                )
                return None
            elif ollama_list_of_models and use_local_models:
                if not model:
                    if len(ollama_list_of_models) > 1:
                        console.print(
                            "[yellow]Select a local model:[/yellow]\n"
                            + "\n".join(
                                [
                                    f"[magenta]{i + 1}. {model}[/magenta]"
                                    for i, model in enumerate(ollama_list_of_models)  # noqa
                                ]
                            ),
                            highlight=False,
                        )
                        model_is_selected = False
                        while not model_is_selected:
                            model = prompt.ask(
                                "[yellow]Enter a number from 1 to "
                                f"{len(ollama_list_of_models)}[/yellow]",
                            )
                            if not (1 <= model <= len(ollama_list_of_models)):
                                console.print(
                                    "[red]Enter a valid number![/red]",
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
                            f"[red]{model} is not an available model!"
                            "[/red] "
                            "Available models: [yellow]"
                            f"{', '.join(ollama_list_of_models)}[/yellow]",
                            highlight=False,
                        )
                        return None
            if model:
                console.print(
                    f"Selected model: [yellow]{model}[/yellow]",
                    highlight=False,
                )
            # Create AI client
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
                        "[magenta bold]Generating commit message...",
                        spinner_style="magenta",
                    ):
                        commit_message = cut_think(
                            client.message(
                                messages=[
                                    {
                                        "role": "system",
                                        "content": prompt_for_ai,
                                    },
                                    {
                                        "role": "user",
                                        "content": "Git status: "
                                        + git_status.stdout
                                        + "Git diff: "
                                        + git_diff.stdout,
                                    },
                                ],
                                temperature=temperature,
                                timeout=timeout,
                            )
                        )
                    commit_with_message_from_ai = input(
                        "Commit with message "
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
                        "Commit created successfully!",
                        style="green bold",
                        highlight=False,
                    )
            else:
                with console.status(
                    "[magenta bold]Generating commit message...",
                    spinner_style="magenta",
                ):
                    commit_message = cut_think(
                        client.message(
                            messages=[
                                {
                                    "role": "system",
                                    "content": prompt_for_ai,
                                },
                                {
                                    "role": "user",
                                    "content": "Git status: "
                                    + git_status.stdout
                                    + "Git diff: "
                                    + git_diff.stdout,
                                },
                            ],
                            temperature=temperature,
                            timeout=timeout,
                        )
                    )
                console.print(commit_message, style="yellow", highlight=False)
                return None

        # If .git does not exist
        else:
            init_git_repo = (
                True
                if input(
                    colored("Git repository not initialized!", "red")
                    + " Run "
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
                        "Make first commit with message "
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
