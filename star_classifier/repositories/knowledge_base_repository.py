"""JSON repository for the knowledge base."""

from __future__ import annotations

import json
from copy import deepcopy

from star_classifier.defaults import build_default_knowledge_base
from star_classifier.runtime import RuntimePaths
from star_classifier.utils.formatting import ensure_parent


class KnowledgeBaseRepository:
    def __init__(self, paths: RuntimePaths):
        self.paths = paths
        self.seed_data_dir = self.paths.bundled_data_dir
        self.seed_default_path = self.seed_data_dir / 'knowledge_base.default.json'
        self.seed_working_path = self.seed_data_dir / 'knowledge_base.json'
        self.data_dir = self.paths.data_dir
        self.working_path = self.data_dir / 'knowledge_base.json'
        self._ensure_seed_files()

    def _default_payload(self) -> str:
        if self.seed_default_path.exists():
            return self.seed_default_path.read_text(encoding='utf-8')
        return json.dumps(build_default_knowledge_base(), ensure_ascii=False, indent=2)

    def _working_seed_payload(self) -> str:
        if self.seed_working_path.exists():
            return self.seed_working_path.read_text(encoding='utf-8')
        return self._default_payload()

    def _ensure_seed_files(self) -> None:
        ensure_parent(self.working_path)
        if not self.working_path.exists():
            self.working_path.write_text(self._working_seed_payload(), encoding='utf-8')

    def load(self) -> dict:
        return json.loads(self.working_path.read_text(encoding='utf-8'))

    def save(self, data: dict) -> None:
        ensure_parent(self.working_path)
        self.working_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def reset_to_defaults(self) -> dict:
        data = json.loads(self._default_payload())
        self.save(data)
        return deepcopy(data)

    def load_defaults(self) -> dict:
        return json.loads(self._default_payload())
