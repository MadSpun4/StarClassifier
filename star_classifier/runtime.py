"""Runtime path helpers for source and frozen builds."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


APP_STORAGE_DIRNAME = 'StarClassifier'
APP_STORAGE_ENV = 'STAR_CLASSIFIER_HOME'


@dataclass(frozen=True)
class RuntimePaths:
    resource_root: Path
    state_root: Path

    @property
    def bundled_data_dir(self) -> Path:
        return self.resource_root / 'data'

    @property
    def bundled_models_dir(self) -> Path:
        return self.resource_root / 'models'

    @property
    def data_dir(self) -> Path:
        return self.state_root / 'data'

    @property
    def models_dir(self) -> Path:
        return self.state_root / 'models'


def _state_root_from_env() -> Path | None:
    override = os.environ.get(APP_STORAGE_ENV)
    if not override:
        return None
    return Path(override).expanduser()


def _default_state_root() -> Path:
    override = _state_root_from_env()
    if override is not None:
        return override
    local_appdata = os.environ.get('LOCALAPPDATA')
    if local_appdata:
        return Path(local_appdata) / APP_STORAGE_DIRNAME
    return Path.home() / f'.{APP_STORAGE_DIRNAME.lower()}'


def resolve_runtime_paths(project_root: Path | None = None) -> RuntimePaths:
    if getattr(sys, 'frozen', False):
        resource_root = Path(getattr(sys, '_MEIPASS', Path(sys.executable).resolve().parent))
        state_root = _default_state_root()
    else:
        resource_root = Path(project_root or Path(__file__).resolve().parents[1])
        state_root = resource_root
    return RuntimePaths(
        resource_root=resource_root.resolve(),
        state_root=state_root.resolve(),
    )
