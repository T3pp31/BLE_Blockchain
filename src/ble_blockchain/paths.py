from pathlib import Path


def repo_root() -> Path:
    """Return the repository root directory (parent of ``src/``)."""
    return Path(__file__).resolve().parent.parent.parent
