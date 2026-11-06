from commands.phonetic import soundex, metaphone_simple, phonetic_similarity, phrase_phonetic_distance
from commands.parser import CommandParser
from commands.normalizer import CommandNormalizer

def test_soundex_basic():
    assert soundex("explorer") == soundex("exploring")
    assert soundex("chrome") == soundex("crome")
    assert soundex("") == ""

def test_metaphone_simple():
    assert metaphone_simple("chrome") == "KRM"
    assert metaphone_simple("crome") == "KRM"
    assert metaphone_simple("phone") == "FN"

def test_phrase_phonetic_distance():
    d1 = phrase_phonetic_distance("open file year", "open file explorer")
    assert d1 >= 0.70

    d2 = phrase_phonetic_distance("open crome", "open chrome")
    assert d2 >= 0.85

    d3 = phrase_phonetic_distance("shoot down", "shutdown")
    assert d3 >= 0.75

def test_parser_with_acoustic_confusions():
    parser = CommandParser()

    intent, params, _ = parser.parse("open file year")
    assert intent == "OPEN_EXPLORER"

    intent, params, _ = parser.parse("open crome")
    assert intent == "OPEN_APP"
    assert params["app"] == "chrome"

    intent, params, _ = parser.parse("shoot down")
    assert intent == "SHUTDOWN"

    intent, params, _ = parser.parse("go to see drive")
    assert intent == "NAVIGATE_DRIVE"
    assert params["drive"] == "c"

    intent, params, _ = parser.parse("stand by")
    assert intent == "GO_TO_SLEEP"

    intent, params, _ = parser.parse("way cup")
    assert intent == "WAKE_UP"
