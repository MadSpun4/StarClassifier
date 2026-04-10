"""Application entry point."""

from __future__ import annotations

from pathlib import Path

from star_classifier.app import StarClassifierApp


if __name__ == '__main__':
    app = StarClassifierApp(Path(__file__).resolve().parent)
    app.mainloop()
