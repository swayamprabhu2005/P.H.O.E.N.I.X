import os
import pytest
from ai.groq_client import GroqClient
from commands.parser import CommandParser
from execution.executor import CommandExecutor
from memory.memory_manager import MemoryManager

def test_memory_manager_website_matching(tmp_path):
    mem_file = os.path.join(tmp_path, "memory.json")
    mgr = MemoryManager(memory_file_path=mem_file)
    mgr.record_website("https://chatgpt.com", "ChatGPT")

    # Match exact and variations
    match = mgr.find_website_match("chat gpt")
    assert match is not None
    assert match["url"] == "https://chatgpt.com"
    assert match["name"] == "ChatGPT"

    # Match dot com
    match2 = mgr.find_website_match("chatgpt.com")
    assert match2 is not None

def test_memory_manager_phrases(tmp_path):
    mem_file = os.path.join(tmp_path, "memory.json")
    mgr = MemoryManager(memory_file_path=mem_file)
    mgr.record_website("https://chatgpt.com", "ChatGPT")
    mgr.record_search("Python tutorials")

    phrases = mgr.get_known_phrases()
    assert "chatgpt" in phrases
    assert "python tutorials" in phrases

def test_groq_client_graceful_fallback():
    client = GroqClient(api_key="")
    assert not client.is_available()
    res = client.disambiguate_query("open chatgpt")
    assert res is None

def test_parser_grammar_includes_drives_and_confirmations():
    parser = CommandParser()
    phrases = parser.get_grammar_phrases()

    # Drives C, D, E
    assert "c drive" in phrases
    assert "d drive" in phrases
    assert "e drive" in phrases
    assert "open c drive" in phrases

    # Confirmations
    assert "yes" in phrases
    assert "no" in phrases
    assert "open chrome" in phrases

def test_drive_navigation_restrictions():
    executor = CommandExecutor()
    # Supported drives
    ok, msg, speech = executor.execute("NAVIGATE_DRIVE", {"drive": "C"})
    assert ok or "not found" in msg.lower() or "not available" in speech.lower()

    # Unsupported drive (e.g. Z or X)
    ok_z, msg_z, speech_z = executor.execute("NAVIGATE_DRIVE", {"drive": "Z"})
    assert not ok_z
    assert "Only C, D, and E drives are supported" in msg_z
