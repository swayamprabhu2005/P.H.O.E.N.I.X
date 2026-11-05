import os
import urllib.request
import zipfile

MODEL_DIR_NAME = "vosk-model-small-en-us-0.15"
MODEL_ZIP_NAME = "vosk-model-small-en-us-0.15.zip"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

def ensure_model_installed(project_root: str) -> str:
    """
    Ensures the Vosk speech model is present in the local project directory.
    If missing (e.g. after fresh git clone), automatically downloads and extracts it.
    """
    models_dir = os.path.join(project_root, "models")
    os.makedirs(models_dir, exist_ok=True)

    target_model_path = os.path.join(models_dir, MODEL_DIR_NAME)
    if os.path.exists(target_model_path):
        return target_model_path

    print("=" * 60)
    print("   P.H.O.E.N.I.X. First-Time Setup: Downloading Voice Model")
    print(f"   Downloading Vosk model to: {models_dir}")
    print("=" * 60)

    zip_path = os.path.join(models_dir, MODEL_ZIP_NAME)

    try:
        def _reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = f"\r   Downloading: {percent:5.1f}% [{readsofar / (1024*1024):.1f} MB / {totalsize / (1024*1024):.1f} MB]"
                print(s, end="", flush=True)

        urllib.request.urlretrieve(MODEL_URL, zip_path, _reporthook)
        print("\n   Download complete. Extracting model...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(models_dir)

        if os.path.exists(zip_path):
            os.remove(zip_path)

        print(f"   [SUCCESS] Model ready at: {target_model_path}")
        return target_model_path

    except Exception as e:
        print(f"\n   [ERROR] Failed to auto-download model: {e}")
        raise e

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ensure_model_installed(root)
