import os
import tempfile
import unittest
from execution.file_ops import FileOperations

class TestFileOperations(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_create_folder(self):
        ok, msg = FileOperations.create_folder(self.temp_dir, "Projects")
        self.assertTrue(ok)
        self.assertTrue(os.path.isdir(os.path.join(self.temp_dir, "Projects")))

    def test_create_text_file(self):
        ok, msg = FileOperations.create_text_file(self.temp_dir, "todo")
        self.assertTrue(ok)
        target = os.path.join(self.temp_dir, "todo.txt")
        self.assertTrue(os.path.isfile(target))
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("P.H.O.E.N.I.X.", content)

    def test_create_word_file(self):
        ok, msg = FileOperations.create_word_file(self.temp_dir, "report")
        self.assertTrue(ok)
        target = os.path.join(self.temp_dir, "report.docx")
        self.assertTrue(os.path.isfile(target))

    def test_open_file_not_found(self):
        ok, msg = FileOperations.open_file_by_name(self.temp_dir, "nonexistent", ".pdf")
        self.assertFalse(ok)
        self.assertIn("not found", msg)

    def test_rename_item(self):
        FileOperations.create_folder(self.temp_dir, "OldFolder")
        ok, msg = FileOperations.rename_item(self.temp_dir, "oldfolder", "NewFolder")
        self.assertTrue(ok)
        self.assertTrue(os.path.isdir(os.path.join(self.temp_dir, "NewFolder")))
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "OldFolder")))

    def test_delete_item(self):
        FileOperations.create_text_file(self.temp_dir, "temp.txt")
        ok, msg = FileOperations.delete_item(self.temp_dir, "temp.txt")
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "temp.txt")))

if __name__ == "__main__":
    unittest.main()
