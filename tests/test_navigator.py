import os
import tempfile
import unittest
from commands.navigator import SystemNavigator

class TestSystemNavigator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sub_folder = os.path.join(self.temp_dir, "TestSub")
        os.makedirs(self.sub_folder, exist_ok=True)
        self.nav = SystemNavigator(initial_directory=self.temp_dir)

    def tearDown(self):
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_initial_directory(self):
        self.assertEqual(os.path.normpath(self.nav.get_current_directory()), os.path.normpath(self.temp_dir))

    def test_open_subfolder(self):
        ok = self.nav.open_folder("testsub")  # case-insensitive check
        self.assertTrue(ok)
        self.assertEqual(os.path.normpath(self.nav.get_current_directory()), os.path.normpath(self.sub_folder))

    def test_go_back(self):
        self.nav.open_folder("TestSub")
        ok = self.nav.go_back()
        self.assertTrue(ok)
        self.assertEqual(os.path.normpath(self.nav.get_current_directory()), os.path.normpath(self.temp_dir))

if __name__ == "__main__":
    unittest.main()
