import os
import shutil
from typing import Tuple

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class FileOperations:
    """Handles local creation and opening of directories, text, Word, and PDF files."""

    @staticmethod
    def create_folder(target_dir: str, folder_name: str) -> Tuple[bool, str]:
        path = os.path.join(target_dir, folder_name.strip())
        try:
            if os.path.exists(path):
                return False, f"Folder '{folder_name}' already exists."
            os.makedirs(path, exist_ok=True)
            return True, f"Folder '{folder_name}' created."
        except Exception as e:
            return False, f"Failed to create folder: {str(e)}"

    @staticmethod
    def create_text_file(target_dir: str, filename: str) -> Tuple[bool, str]:
        name = filename.strip()
        if not name.lower().endswith(".txt"):
            name += ".txt"
        path = os.path.join(target_dir, name)
        try:
            if os.path.exists(path):
                return False, f"File '{name}' already exists."
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {name}\nCreated by P.H.O.E.N.I.X. Assistant\n")
            return True, f"Text file '{name}' created."
        except Exception as e:
            return False, f"Failed to create text file: {str(e)}"

    @staticmethod
    def create_word_file(target_dir: str, filename: str) -> Tuple[bool, str]:
        name = filename.strip()
        if not name.lower().endswith(".docx"):
            name += ".docx"
        path = os.path.join(target_dir, name)
        try:
            if os.path.exists(path):
                return False, f"Document '{name}' already exists."

            if DOCX_AVAILABLE:
                doc = Document()
                doc.add_heading(name.replace(".docx", ""), level=0)
                doc.add_paragraph("Document created with P.H.O.E.N.I.X. Desktop Assistant.")
                doc.save(path)
            else:
                with open(path, "wb") as f:
                    f.write(b"")

            return True, f"Word file '{name}' created."
        except Exception as e:
            return False, f"Failed to create Word document: {str(e)}"

    @staticmethod
    def create_generic_file(target_dir: str, filename: str) -> Tuple[bool, str]:
        name = filename.strip()
        path = os.path.join(target_dir, name)
        try:
            if os.path.exists(path):
                return False, f"File '{name}' already exists."
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
            return True, f"File '{name}' created."
        except Exception as e:
            return False, f"Failed to create file: {str(e)}"

    @staticmethod
    def open_file_by_name(target_dir: str, filename: str, expected_ext: str = "") -> Tuple[bool, str]:
        """Finds and launches file by name in target directory."""
        query = filename.strip().lower()
        if expected_ext and not expected_ext.startswith("."):
            expected_ext = "." + expected_ext

        # Exact match attempt
        candidate = None
        try:
            for item in os.listdir(target_dir):
                item_lower = item.lower()
                # Check exact name or name with expected extension
                if item_lower == query or (expected_ext and item_lower == f"{query}{expected_ext}"):
                    candidate = os.path.join(target_dir, item)
                    break
                # Check starts with query and ends with expected extension
                if expected_ext and item_lower.endswith(expected_ext) and query in item_lower:
                    candidate = os.path.join(target_dir, item)
                    break

            if candidate and os.path.isfile(candidate):
                os.startfile(candidate)
                return True, f"Opened {os.path.basename(candidate)}"

            return False, f"File '{filename}' not found in current directory."
        except Exception as e:
            return False, f"Failed to open file: {e}"

    @staticmethod
    def rename_item(target_dir: str, old_name: str, new_name: str) -> Tuple[bool, str]:
        old_path = os.path.join(target_dir, old_name.strip())
        new_path = os.path.join(target_dir, new_name.strip())

        if not os.path.exists(old_path):
            found = False
            for item in os.listdir(target_dir):
                if item.lower() == old_name.strip().lower():
                    old_path = os.path.join(target_dir, item)
                    found = True
                    break
            if not found:
                return False, f"Item '{old_name}' not found."

        try:
            os.rename(old_path, new_path)
            return True, f"Renamed '{old_name}' to '{new_name}'."
        except Exception as e:
            return False, f"Failed to rename: {str(e)}"

    @staticmethod
    def delete_item(target_dir: str, item_name: str) -> Tuple[bool, str]:
        path = os.path.join(target_dir, item_name.strip())
        if not os.path.exists(path):
            return False, f"Item '{item_name}' does not exist."
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return True, f"'{item_name}' deleted."
        except Exception as e:
            return False, f"Failed to delete: {str(e)}"
