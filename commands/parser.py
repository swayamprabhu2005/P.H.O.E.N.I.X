import json
import os
import re
from typing import Optional, Tuple, Dict, Any
from commands.normalizer import CommandNormalizer

class CommandParser:
    """Parses speech or text into structured intents and parameters, preserving parameter casing."""

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_path = os.path.join(base_dir, "commands", "command_registry.json")

        self.registry_path = registry_path
        self.intents = []
        self._compiled_rules = []
        self._load_registry()

    def _load_registry(self):
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.intents = data.get("intents", [])
        self._compiled_rules = []

        for item in self.intents:
            intent = item["intent"]
            patterns = item["patterns"]
            param_defs = item.get("params", {})
            feedback = item.get("feedback", "")

            for pat in patterns:
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

        # First, try matching directly against stripped text to preserve original parameter casing
        cleaned_raw = text.strip()
        for prefix in CommandNormalizer.FILLER_PREFIXES:
            cleaned_raw = re.sub(prefix, "", cleaned_raw, flags=re.IGNORECASE).strip()

        for regex, intent, feedback in self._compiled_rules:
            match = regex.match(cleaned_raw)
            if match:
                params = match.groupdict()
                cleaned_params = {k: v.strip(" '\"") for k, v in params.items() if v}
                return intent, cleaned_params, feedback

        # Fallback to normalized text
        normalized = CommandNormalizer.normalize(text)
        for regex, intent, feedback in self._compiled_rules:
            match = regex.match(normalized)
            if match:
                params = match.groupdict()
                cleaned_params = {k: v.strip(" '\"") for k, v in params.items() if v}
                return intent, cleaned_params, feedback

        return None, {}, "Command not recognized."
