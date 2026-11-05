import re
import string

class CommandNormalizer:
    """Normalizes recognized speech text for deterministic pattern matching."""

    FILLER_PREFIXES = [
        r"^(please\s+)",
        r"^(can\s+you\s+please\s+)",
        r"^(can\s+you\s+)",
        r"^(could\s+you\s+)",
        r"^(would\s+you\s+)",
        r"^(phoenix\s+)",
        r"^(hey\s+phoenix\s+)",
        r"^(ok\s+phoenix\s+)",
        r"^(just\s+)",
    ]

    SYNONYMS = {
        "google chrome": "chrome",
        "microsoft edge": "edge",
        "file manager": "file explorer",
        "this pc": "file explorer",
        "doc file": "word file",
        "docx file": "word file",
        "powerpoint": "powerpoint",
        "powerpoint presentation": "presentation",
        "ppt file": "presentation",
        "pptx file": "presentation",
        "txt file": "text file",
        "account one": "account 1",
        "account two": "account 2",
        "account three": "account 3",
        "account four": "account 4",
        "account five": "account 5",
        "first account": "account 1",
        "second account": "account 2",
        "third account": "account 3",
        "fourth account": "account 4",
        "fifth account": "account 5",
        "first email": "account 1",
        "second email": "account 2",
        "third email": "account 3",
        "fourth email": "account 4",
        "fifth email": "account 5",
    }

    @classmethod
    def normalize(cls, raw_text: str) -> str:
        if not raw_text:
            return ""

        text = raw_text.strip().lower()

        # Remove punctuation except periods and underscores that might belong to file names
        for char in string.punctuation:
            if char not in (".", "_", "-"):
                text = text.replace(char, " ")

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove leading polite fillers
        for prefix in cls.FILLER_PREFIXES:
            text = re.sub(prefix, "", text, flags=re.IGNORECASE).strip()

        # Apply phrase synonyms
        for phrase, replacement in cls.SYNONYMS.items():
            pattern = r"\b" + re.escape(phrase) + r"\b"
            text = re.sub(pattern, replacement, text)

        return text
