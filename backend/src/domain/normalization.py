import re
import unicodedata


def normalize(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text)
    text = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"\b[a-z]'", "", text)
    text = re.sub(r"'", "", text)
    text = re.sub(r"-", " ", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return " ".join(text.split())
