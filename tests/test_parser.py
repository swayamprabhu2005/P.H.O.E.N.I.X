import unittest
from commands.parser import CommandParser

class TestCommandParser(unittest.TestCase):

    def setUp(self):
        self.parser = CommandParser()

    def test_lifecycle_and_user_name(self):
        intent, params, _ = self.parser.parse("stop")
        self.assertEqual(intent, "GO_TO_SLEEP")

        intent, params, _ = self.parser.parse("go to sleep")
        self.assertEqual(intent, "GO_TO_SLEEP")

        intent, params, _ = self.parser.parse("shutdown")
        self.assertEqual(intent, "SHUTDOWN")

        intent, params, _ = self.parser.parse("call me Swayam")
        self.assertEqual(intent, "CHANGE_USER_NAME")
        self.assertEqual(params.get("name"), "Swayam")

    def test_terminals_and_modes(self):
        intent, _, _ = self.parser.parse("open command prompt")
        self.assertEqual(intent, "OPEN_CMD")

        intent, _, _ = self.parser.parse("open powershell")
        self.assertEqual(intent, "OPEN_POWERSHELL")

        intent, _, _ = self.parser.parse("coding mode vs code")
        self.assertEqual(intent, "CODING_MODE_VSCODE")

        intent, _, _ = self.parser.parse("coding mode antigravity")
        self.assertEqual(intent, "CODING_MODE_ANTIGRAVITY")

        intent, _, _ = self.parser.parse("learning mode chatgpt")
        self.assertEqual(intent, "LEARNING_MODE_CHATGPT")

        intent, _, _ = self.parser.parse("learning mode perplexity")
        self.assertEqual(intent, "LEARNING_MODE_PERPLEXITY")

    def test_google_services_and_accounts(self):
        intent, _, _ = self.parser.parse("open email")
        self.assertEqual(intent, "OPEN_EMAIL")

        intent, _, _ = self.parser.parse("open google drive")
        self.assertEqual(intent, "OPEN_GOOGLE_DRIVE")

        # Test account number switching (supports 1, 2, 3, 4, 5, etc.)
        intent, params, _ = self.parser.parse("switch to account 1")
        self.assertEqual(intent, "SWITCH_GOOGLE_ACCOUNT_NUM")
        self.assertEqual(params.get("num"), "1")

        intent, params, _ = self.parser.parse("switch to account 5")
        self.assertEqual(intent, "SWITCH_GOOGLE_ACCOUNT_NUM")
        self.assertEqual(params.get("num"), "5")

        intent, params, _ = self.parser.parse("second account")
        self.assertEqual(intent, "SWITCH_GOOGLE_ACCOUNT_NUM")
        self.assertEqual(params.get("num"), "2")

        intent, _, _ = self.parser.parse("switch account")
        self.assertEqual(intent, "SWITCH_GOOGLE_ACCOUNT_CHOOSER")

    def test_open_files_by_name(self):
        intent, params, _ = self.parser.parse("open pdf report")
        self.assertEqual(intent, "OPEN_PDF_FILE")
        self.assertEqual(params.get("name"), "report")

        intent, params, _ = self.parser.parse("open word thesis")
        self.assertEqual(intent, "OPEN_WORD_FILE")
        self.assertEqual(params.get("name"), "thesis")

        intent, params, _ = self.parser.parse("open text todo")
        self.assertEqual(intent, "OPEN_TXT_FILE")
        self.assertEqual(params.get("name"), "todo")

        intent, params, _ = self.parser.parse("open presentation slides")
        self.assertEqual(intent, "OPEN_PPT_FILE")
        self.assertEqual(params.get("name"), "slides")

    def test_navigation_intents(self):
        intent, params, _ = self.parser.parse("go to d drive")
        self.assertEqual(intent, "NAVIGATE_DRIVE")
        self.assertEqual(params.get("drive"), "d")

        intent, params, _ = self.parser.parse("open folder Projects")
        self.assertEqual(intent, "OPEN_FOLDER")
        self.assertEqual(params.get("name"), "Projects")

        intent, params, _ = self.parser.parse("go back")
        self.assertEqual(intent, "GO_BACK")

    def test_file_creation_intents(self):
        intent, params, _ = self.parser.parse("create folder MyWork")
        self.assertEqual(intent, "CREATE_FOLDER")
        self.assertEqual(params.get("name"), "MyWork")

        intent, params, _ = self.parser.parse("create text file notes")
        self.assertEqual(intent, "CREATE_TXT_FILE")
        self.assertEqual(params.get("name"), "notes")

        intent, params, _ = self.parser.parse("create word file report")
        self.assertEqual(intent, "CREATE_WORD_FILE")
        self.assertEqual(params.get("name"), "report")

    def test_browser_and_screen_intents(self):
        intent, params, _ = self.parser.parse("copy url")
        self.assertEqual(intent, "COPY_URL")

        intent, params, _ = self.parser.parse("search quantum computing")
        self.assertEqual(intent, "WEB_SEARCH")
        self.assertEqual(params.get("query"), "quantum computing")

        intent, params, _ = self.parser.parse("take screenshot")
        self.assertEqual(intent, "TAKE_SCREENSHOT")

        intent, params, _ = self.parser.parse("activate snipping tool")
        self.assertEqual(intent, "SNIPPING_TOOL")

    def test_windows_shortcut_intents(self):
        intent, params, _ = self.parser.parse("show desktop")
        self.assertEqual(intent, "SHOW_DESKTOP")

        intent, params, _ = self.parser.parse("open clipboard")
        self.assertEqual(intent, "OPEN_CLIPBOARD")

        intent, params, _ = self.parser.parse("lock pc")
        self.assertEqual(intent, "LOCK_PC")

        intent, params, _ = self.parser.parse("next page")
        self.assertEqual(intent, "NEXT_PAGE")

    def test_unregistered_ambient_speech_returns_none(self):
        # Non-registered spoken phrases must return None to trigger silent rejection
        intent, params, feedback = self.parser.parse("what is the weather in Paris today")
        self.assertIsNone(intent)

        intent, params, feedback = self.parser.parse("hello how are you doing")
        self.assertIsNone(intent)

        intent, params, feedback = self.parser.parse("random ambient conversation in the room")
        self.assertIsNone(intent)

if __name__ == "__main__":
    unittest.main()
