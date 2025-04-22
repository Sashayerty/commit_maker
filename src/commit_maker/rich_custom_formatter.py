# Кастомный форматтер для --help
import rich_argparse


class CustomFormatter(rich_argparse.RichHelpFormatter):
    styles = {
        "argparse.args": "cyan bold",
        "argparse.groups": "green bold",
        "argparse.metavar": "dark_cyan",
        "argparse.prog": "dark_green bold",
    }
