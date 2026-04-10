"""JSON repository for the knowledge base."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from star_classifier.defaults import build_default_knowledge_base
from star_classifier.utils.formatting import ensure_parent


class KnowledgeBaseRepository:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.data_dir = self.project_dir / 'data'
        self.default_path = self.data_dir / 'knowledge_base.default.json'
        self.working_path = self.data_dir / 'knowledge_base.json'
        self._ensure_seed_files()

    def _ensure_seed_files(self) -> None:
        ensure_parent(self.default_path)
        if not self.default_path.exists():
            self.default_path.write_text(
                json.dumps(build_default_knowledge_base(), ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
        if not self.working_path.exists():
            self.working_path.write_text(self.default_path.read_text(encoding='utf-8'), encoding='utf-8')

    def load(self) -> dict:
        return json.loads(self.working_path.read_text(encoding='utf-8'))

    def save(self, data: dict) -> None:
        ensure_parent(self.working_path)
        self.working_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def reset_to_defaults(self) -> dict:
        data = json.loads(self.default_path.read_text(encoding='utf-8'))
        self.save(data)
        return deepcopy(data)

    def load_defaults(self) -> dict:
        return json.loads(self.default_path.read_text(encoding='utf-8'))
