import difflib
import json
import os
import re
from typing import Optional, Tuple, Dict, Any, List
from commands.normalizer import CommandNormalizer
from commands.phonetic import phrase_phonetic_distance

class CommandParser:
    """Parses speech or text into structured intents and parameters, preserving parameter casing."""

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_path = os.path.join(base_dir, "commands", "command_registry.json")

        self.registry_path = registry_path
        self.intents = []
        self._compiled_rules = []
        self._raw_patterns = []  # For fuzzy matching
        self._load_registry()

    def _load_registry(self):
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.intents = data.get("intents", [])
        self._compiled_rules = []
        self._raw_patterns = []

        for item in self.intents:
            intent = item["intent"]
            patterns = item["patterns"]
            param_defs = item.get("params", {})
            feedback = item.get("feedback", "")

            for pat in patterns:
                self._raw_patterns.append((pat, intent, feedback, param_defs))
                # Convert pattern string with placeholders like {name} into regex
                regex_str = "^" + re.escape(pat) + "$"
                for param_name, param_regex in param_defs.items():
                    escaped_placeholder = re.escape("{" + param_name + "}")
                    regex_str = regex_str.replace(escaped_placeholder, f"(?P<{param_name}>{param_regex})")

                compiled = re.compile(regex_str, re.IGNORECASE)
                self._compiled_rules.append((compiled, intent, feedback))

    def parse(self, text: str) -> Tuple[Optional[str], Dict[str, Any], str]:
        if not text:
            return None, {}, ""

        # 1. Direct match on cleaned raw text
        cleaned_raw = text.strip()
        for prefix in CommandNormalizer.FILLER_PREFIXES:
            cleaned_raw = re.sub(prefix, "", cleaned_raw, flags=re.IGNORECASE).strip()

        for regex, intent, feedback in self._compiled_rules:
            match = regex.match(cleaned_raw)
            if match:
                params = match.groupdict()
                cleaned_params = {k: v.strip(" '\"") for k, v in params.items() if v}
                return intent, cleaned_params, feedback

        # 2. Fallback to normalized text
        normalized = CommandNormalizer.normalize(text)
        for regex, intent, feedback in self._compiled_rules:
            match = regex.match(normalized)
            if match:
                params = match.groupdict()
                cleaned_params = {k: v.strip(" '\"") for k, v in params.items() if v}
                return intent, cleaned_params, feedback

        # 3. Fuzzy & Phonetic Distance fallback for static commands (similarity >= 0.72)
        best_ratio = 0.0
        best_intent = None
        best_feedback = ""
        norm_lower = normalized.lower().strip()

        for pat, intent, feedback, param_defs in self._raw_patterns:
            # Only fuzzy & phonetic match patterns without open wildcard params (.+)
            if not param_defs:
                ratio = phrase_phonetic_distance(norm_lower, pat.lower())
                if ratio > best_ratio and ratio >= 0.72:
                    best_ratio = ratio
                    best_intent = intent
                    best_feedback = feedback

        if best_intent:
            return best_intent, {}, best_feedback

        return None, {}, "Command not recognized."

    def get_grammar_phrases(self) -> List[str]:
        """Extracts expanded phrase list for Vosk constrained grammar."""
        phrases = set()

        for item in self.intents:
            patterns = item.get("patterns", [])
            param_defs = item.get("params", {})

            for pat in patterns:
                pat_lower = pat.lower().strip()
                if not param_defs:
                    phrases.add(pat_lower)
                elif "{app}" in pat_lower:
                    apps = ["chrome", "edge", "comet", "notepad", "calculator", "word", "powerpoint", "excel", "task manager", "settings", "snipping tool"]
                    for app in apps:
                        phrases.add(pat_lower.replace("{app}", app))
                elif "{drive}" in pat_lower:
                    drives = ["c", "d", "e"]
                    for drive in drives:
                        phrases.add(pat_lower.replace("{drive}", drive))
                elif "{name}" in pat_lower or "{query}" in pat_lower or "{key}" in pat_lower:
                    # Add base action words
                    base_prefix = re.sub(r"\{.*?\}", "", pat_lower).strip()
                    if base_prefix:
                        phrases.add(base_prefix)

        # Essential short commands and confirmations
        essential = [
            "c drive", "d drive", "e drive",
            "open c drive", "open d drive", "open e drive",
            "go to c drive", "go to d drive", "go to e drive",
            "open chrome", "launch chrome", "start chrome",
            "open file explorer", "open explorer", "open this pc",
            "yes", "yeah", "yep", "correct", "confirm", "proceed", "sure",
            "no", "nope", "cancel", "stop", "abort",
            "standby", "sleep", "wake up", "close phoenix", "shutdown",
            "search", "google", "find"
        ]
        phrases.update(essential)

        return sorted(list(phrases))
