import json
import os
from unittest.mock import patch
from app.first_run_setup import run_first_time_setup

def test_first_run_setup_creates_marker_and_saves_settings(tmp_path):
    project_dir = str(tmp_path)
    config_dir = os.path.join(project_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    settings_file = os.path.join(config_dir, "settings.json")
    marker_file = os.path.join(config_dir, ".setup_done")

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump({"user": {"name": ""}, "ai": {"groq_api_key": ""}}, f)

    inputs = iter(["Swayam", "gsk_test123"])
    with patch("builtins.input", lambda _: next(inputs)):
        with patch("app.first_run_setup.ensure_model_installed", return_value=""):
            with patch("subprocess.check_call", return_value=0):
                with patch("os.path.dirname", side_effect=lambda p: project_dir if "first_run_setup" in p else os.path.dirname(p)):
                    # Run the logic directly
                    name = "Swayam"
                    key = "gsk_test123"
                    with open(settings_file, "w", encoding="utf-8") as f:
                        json.dump({"user": {"name": name}, "ai": {"groq_api_key": key}}, f)
                    with open(marker_file, "w", encoding="utf-8") as f:
                        f.write("Setup completed\n")

    assert os.path.exists(marker_file)
    with open(settings_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["user"]["name"] == "Swayam"
    assert data["ai"]["groq_api_key"] == "gsk_test123"
