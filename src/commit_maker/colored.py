# Функции для цветного вывода/ввода


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
