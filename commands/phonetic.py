import difflib
import re
from typing import List, Tuple, Optional

def soundex(word: str) -> str:
    """Computes standard American Soundex code for an English word."""
    word = word.upper().strip()
    if not word or not word[0].isalpha():
        return ""

    first_char = word[0]
    # Mapping table for consonants
    mapping = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6"
    }

    codes = [first_char]
    prev_code = mapping.get(first_char, "0")

    for ch in word[1:]:
        if not ch.isalpha():
            continue
        code = mapping.get(ch, "0")
        if code != "0":
            if code != prev_code:
                codes.append(code)
            prev_code = code
        else:
            prev_code = "0"

    soundex_code = "".join(codes)
    # Pad with zeros or truncate to length 4
    soundex_code = (soundex_code + "000")[:4]
    return soundex_code

def metaphone_simple(word: str) -> str:
    """Computes simplified Metaphone phonetic representation."""
    word = word.lower().strip()
    if not word:
        return ""

    # Drop non-alphas
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return ""

    # Initial sound transformations
    if word.startswith(("kn", "gn", "pn", "wr")):
        word = word[1:]
    elif word.startswith("x"):
        word = "s" + word[1:]
    elif word.startswith("wh"):
        word = "w" + word[2:]

    res = []
    i = 0
    length = len(word)

    while i < length:
        ch = word[i]
        # Skip duplicate consecutive characters (except 'c')
        if i > 0 and ch == word[i - 1] and ch != "c":
            i += 1
            continue

        if ch in ("a", "e", "i", "o", "u"):
            if i == 0:
                res.append(ch.upper())
        elif ch == "b":
            if not (i == length - 1 and i > 0 and word[i - 1] == "m"):
                res.append("B")
        elif ch == "c":
            if i + 1 < length and word[i + 1] in ("e", "i", "y"):
                res.append("S")
            elif i + 1 < length and word[i + 1] == "h":
                if i + 2 < length and word[i + 2] in ("r", "l"):
                    res.append("K")
                else:
                    res.append("X")
                i += 1
            else:
                res.append("K")
        elif ch == "d":
            if i + 1 < length and word[i + 1] == "g" and i + 2 < length and word[i + 2] in ("e", "i", "y"):
                res.append("J")
                i += 2
            else:
                res.append("T")
        elif ch in ("f", "v"):
            res.append("F")
        elif ch in ("g", "j"):
            if i + 1 < length and word[i + 1] == "h":
                i += 1
            else:
                res.append("K" if ch == "g" and (i + 1 == length or word[i + 1] not in ("e", "i", "y")) else "J")
        elif ch == "k":
            res.append("K")
        elif ch == "l":
            res.append("L")
        elif ch in ("m", "n"):
            res.append(ch.upper())
        elif ch == "p":
            if i + 1 < length and word[i + 1] == "h":
                res.append("F")
                i += 1
            else:
                res.append("P")
        elif ch == "q":
            res.append("K")
        elif ch == "r":
            res.append("R")
        elif ch == "s":
            if i + 1 < length and word[i + 1] == "h":
                res.append("X")
                i += 1
            else:
                res.append("S")
        elif ch == "t":
            if i + 1 < length and word[i + 1] == "h":
                res.append("0")
                i += 1
            else:
                res.append("T")
        elif ch == "w":
            if i + 1 < length and word[i + 1] in ("a", "e", "i", "o", "u"):
                res.append("W")
        elif ch == "x":
            res.append("KS")
        elif ch == "y":
            if i + 1 < length and word[i + 1] in ("a", "e", "i", "o", "u"):
                res.append("Y")
        elif ch == "z":
            res.append("S")

        i += 1

    return "".join(res)

def phonetic_similarity(word1: str, word2: str) -> float:
    """Calculates phonetic similarity (0.0 to 1.0) between two individual words."""
    if word1 == word2:
        return 1.0

    s1 = soundex(word1)
    s2 = soundex(word2)
    soundex_match = (s1 == s2 and s1 != "")

    m1 = metaphone_simple(word1)
    m2 = metaphone_simple(word2)
    metaphone_ratio = difflib.SequenceMatcher(None, m1, m2).ratio() if (m1 and m2) else 0.0
    text_ratio = difflib.SequenceMatcher(None, word1, word2).ratio()

    # Blend phonetic and character distance
    if soundex_match and metaphone_ratio >= 0.8:
        return max(0.90, text_ratio)

    return max(metaphone_ratio * 0.65 + text_ratio * 0.35, text_ratio)

def phrase_phonetic_distance(phrase1: str, phrase2: str) -> float:
    """Calculates word-token and phonetic alignment distance between two phrases."""
    tokens1 = phrase1.lower().strip().split()
    tokens2 = phrase2.lower().strip().split()

    if not tokens1 or not tokens2:
        return 0.0

    # Character level baseline
    char_ratio = difflib.SequenceMatcher(None, phrase1.lower().strip(), phrase2.lower().strip()).ratio()

    # If token lengths match exactly:
    if len(tokens1) == len(tokens2):
        scores = [phonetic_similarity(t1, t2) for t1, t2 in zip(tokens1, tokens2)]
        token_avg = sum(scores) / len(scores)
        return max(char_ratio, token_avg)

    # If one phrase is a prefix of another or has insertion/deletion
    matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
    token_ratio = matcher.ratio()

    return max(char_ratio, token_ratio)
