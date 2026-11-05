import unittest
from commands.normalizer import CommandNormalizer

class TestCommandNormalizer(unittest.TestCase):

    def test_casing_and_whitespace(self):
        self.assertEqual(CommandNormalizer.normalize("  OPEN   CHROME  "), "open chrome")

    def test_stripping_polite_fillers(self):
        self.assertEqual(CommandNormalizer.normalize("Please open Chrome"), "open chrome")
        self.assertEqual(CommandNormalizer.normalize("Can you please create folder Test"), "create folder test")
        self.assertEqual(CommandNormalizer.normalize("Phoenix wake up"), "wake up")
        self.assertEqual(CommandNormalizer.normalize("Hey Phoenix take screenshot"), "take screenshot")

    def test_synonyms(self):
        self.assertEqual(CommandNormalizer.normalize("open google chrome"), "open chrome")
        self.assertEqual(CommandNormalizer.normalize("open microsoft edge"), "open edge")
        self.assertEqual(CommandNormalizer.normalize("create doc file report"), "create word file report")
        self.assertEqual(CommandNormalizer.normalize("create ppt file slides"), "create presentation slides")

if __name__ == "__main__":
    unittest.main()
