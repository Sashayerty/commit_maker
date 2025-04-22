# Кастомный класс промпта
import rich.prompt


class CustomIntPrompt(rich.prompt.IntPrompt):
    validate_error_message = "[red]Введите число![/red]"
