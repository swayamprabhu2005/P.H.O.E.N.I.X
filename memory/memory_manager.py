import json
import os
import re
from typing import List, Dict, Any, Optional

class MemoryManager:
    """Manages persistent memory of visited websites, search queries, and recent files."""

    def __init__(self, memory_file_path: Optional[str] = None):
        if memory_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            memory_file_path = os.path.join(base_dir, "config", "memory.json")

        self.memory_file_path = memory_file_path
        self.data: Dict[str, Any] = {
            "visited_websites": [],
            "recent_searches": [],
            "recent_files": []
        }
        self.load()

    def load(self):
        """Loads memory data from JSON file."""
        if os.path.exists(self.memory_file_path):
            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
        else:
            self.save()

    def save(self):
        """Persists memory data to disk."""
        os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
        try:
            with open(self.memory_file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def record_website(self, url: str, name: Optional[str] = None):
        """Records or updates a website visit."""
        url_clean = url.strip()
        if not url_clean:
            return

        if not name:
            domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url_clean)
            name = domain_match.group(1).split(".")[0].title() if domain_match else "Website"

        websites = self.data.setdefault("visited_websites", [])
        found = False
        for site in websites:
            if site.get("url", "").rstrip("/") == url_clean.rstrip("/"):
                site["visits"] = site.get("visits", 0) + 1
                found = True
                break

        if not found:
            keywords = [name.lower(), name.lower().replace(" ", "")]
            websites.append({
                "url": url_clean,
                "name": name,
                "keywords": keywords,
                "visits": 1
            })

        # Keep sorted by visit count
        websites.sort(key=lambda s: s.get("visits", 0), reverse=True)
        self.save()

    def record_search(self, query: str):
        """Records a search query in recent searches."""
        query_clean = query.strip()
        if not query_clean:
            return

        searches = self.data.setdefault("recent_searches", [])
        if query_clean in searches:
            searches.remove(query_clean)
        searches.insert(0, query_clean)
        if len(searches) > 30:
            self.data["recent_searches"] = searches[:30]
        self.save()

    def record_file(self, filename: str):
        """Records an accessed or created file name."""
        name_clean = filename.strip()
        if not name_clean:
            return

        files = self.data.setdefault("recent_files", [])
        if name_clean in files:
            files.remove(name_clean)
        files.insert(0, name_clean)
        if len(files) > 30:
            self.data["recent_files"] = files[:30]
        self.save()

    def find_website_match(self, spoken_text: str) -> Optional[Dict[str, Any]]:
        """Matches spoken text against visited websites keywords."""
        if not spoken_text:
            return None

        cleaned = spoken_text.lower().replace(".", " ").replace("dot com", "").replace(".com", "").strip()
        cleaned_compact = cleaned.replace(" ", "")
        websites = self.data.get("visited_websites", [])

        # 1. Exact name match (space-agnostic)
        for site in websites:
            name = site.get("name", "").lower()
            name_compact = name.replace(" ", "")
            if name == cleaned or name in cleaned or name_compact == cleaned_compact or name_compact in cleaned_compact:
                return site

        # 2. Keyword match
        for site in websites:
            for kw in site.get("keywords", []):
                kw_lower = kw.lower()
                kw_compact = kw_lower.replace(" ", "")
                if kw_lower in cleaned or cleaned in kw_lower or kw_compact in cleaned_compact or cleaned_compact in kw_compact:
                    return site

        return None

    def get_known_phrases(self) -> List[str]:
        """Returns list of website names and recent terms to enrich voice grammar."""
        phrases = set()
        for site in self.data.get("visited_websites", []):
            name = site.get("name", "").lower().strip()
            if name:
                phrases.add(name)
                phrases.add(f"{name} dot com")
                phrases.add(f"open {name}")
                phrases.add(f"search {name}")
            for kw in site.get("keywords", []):
                if kw:
                    phrases.add(kw)

        for s in self.data.get("recent_searches", []):
            s_clean = s.lower().strip()
            if s_clean and len(s_clean.split()) <= 4:
                phrases.add(s_clean)
                phrases.add(f"search {s_clean}")

        return list(phrases)
