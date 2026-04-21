"""Application entry point."""

from __future__ import annotations

from pathlib import Path

from star_classifier.app import StarClassifierApp
from star_classifier.runtime import resolve_runtime_paths


if __name__ == '__main__':
    app = StarClassifierApp(resolve_runtime_paths(Path(__file__).resolve().parent))
    app.mainloop()
