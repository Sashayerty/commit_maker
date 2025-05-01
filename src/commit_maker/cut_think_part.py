import re


def cut_think(message: str) -> str:
    clean = re.sub(r"\s*<think>.*?</think>\s*", "", message, flags=re.DOTALL)
    return clean
