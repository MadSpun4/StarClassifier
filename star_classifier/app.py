"""Root application object."""

from __future__ import annotations

import tkinter as tk

from star_classifier.repositories.knowledge_base_repository import KnowledgeBaseRepository
from star_classifier.runtime import RuntimePaths
from star_classifier.services.expert_classifier import ExpertClassifierService
from star_classifier.services.knowledge_base_service import KnowledgeBaseService
from star_classifier.services.ml_classifier import MlClassifierService
from star_classifier.theme import COLORS, build_fonts
from star_classifier.windows.launcher import LauncherFrame


class StarClassifierApp(tk.Tk):
    def __init__(self, paths: RuntimePaths):
        super().__init__()
        self.paths = paths
        self.title('Классификатор светимости звёзд')
        self.geometry('620x420')
        self.minsize(620, 420)
        self.configure(bg=COLORS['bg'])
        self.fonts = build_fonts()
        repository = KnowledgeBaseRepository(self.paths)
        self.kb_service = KnowledgeBaseService(repository)
        self.ml_service = MlClassifierService(self.paths)
        self.expert_classifier = ExpertClassifierService(self.ml_service)
        launcher = LauncherFrame(
            self,
            kb_service=self.kb_service,
            ml_service=self.ml_service,
            expert_classifier=self.expert_classifier,
        )
        launcher.pack(fill='both', expand=True)
