"""Launcher screen."""

from __future__ import annotations

import tkinter as tk

from star_classifier.services.notifications import error, info
from star_classifier.theme import COLORS
from star_classifier.windows.data_entry import DataEntryWindow
from star_classifier.windows.knowledge_editor import KnowledgeEditorWindow


class LauncherFrame(tk.Frame):
    def __init__(self, master, *, kb_service, ml_service, expert_classifier):
        super().__init__(master, bg=COLORS['bg'])
        self.master = master
        self.kb_service = kb_service
        self.ml_service = ml_service
        self.expert_classifier = expert_classifier
        self.status_var = tk.StringVar()
        self._build()
        self.refresh_status()

    def _build(self):
        card = tk.Frame(self, bg=COLORS['white'], bd=1, relief='solid')
        card.pack(fill='both', expand=True, padx=24, pady=24)

        tk.Label(
            card,
            text='Классификатор светимости звёзд',
            font=self.master.fonts.launcher_heading,
            bg=COLORS['white'],
        ).pack(pady=(24, 10))
        tk.Label(
            card,
            text='Приложение использует редактируемую базу знаний из курсовой документации и ML-модель для разрешения неоднозначных случаев.',
            font=self.master.fonts.launcher_text,
            bg=COLORS['white'],
            justify='center',
            wraplength=480,
        ).pack(pady=(0, 16))

        tk.Label(
            card,
            textvariable=self.status_var,
            font=self.master.fonts.launcher_text,
            fg=COLORS['muted'],
            bg=COLORS['white'],
            justify='center',
            wraplength=500,
        ).pack(pady=(0, 12))

        buttons = tk.Frame(card, bg=COLORS['white'])
        buttons.pack()

        for text, command, bg in [
            ('Открыть редактор базы знаний', self.open_editor, COLORS['gray_btn']),
            ('Открыть ввод исходных данных', self.open_data_entry, COLORS['green']),
            ('Переобучить ML-модель по текущей БЗ', self.retrain_model, COLORS['blue']),
            ('Сбросить базу знаний к значениям из курсовой', self.reset_knowledge_base, COLORS['gray_btn']),
        ]:
            tk.Button(
                buttons,
                text=text,
                bg=bg,
                fg='white' if bg == COLORS['blue'] else COLORS['text'],
                bd=0,
                padx=18,
                pady=10,
                command=command,
                cursor='hand2',
            ).pack(fill='x', pady=8)

    def refresh_status(self):
        report = self.kb_service.validate()
        if self.ml_service.is_compatible(self.kb_service.data):
            meta = self.ml_service.read_metadata()
            ml_status = f"ML-модель готова (accuracy={meta.get('accuracy', 0):.3f}, macro-F1={meta.get('macro_f1', 0):.3f})."
        else:
            ml_status = 'ML-модель отсутствует или не соответствует текущей базе знаний.'
        kb_status = 'База знаний заполнена корректно.' if report.is_valid else 'В базе знаний есть незаполненные поля. Их видно в разделе проверки полноты знаний.'
        self.status_var.set(f'{kb_status}\n{ml_status}')

    def open_editor(self):
        window = KnowledgeEditorWindow(
            self.master,
            kb_service=self.kb_service,
            ml_service=self.ml_service,
            on_data_changed=self.refresh_status,
        )
        window.focus_force()

    def open_data_entry(self):
        window = DataEntryWindow(
            self.master,
            kb_service=self.kb_service,
            expert_classifier=self.expert_classifier,
            ml_service=self.ml_service,
            on_data_changed=self.refresh_status,
        )
        window.focus_force()

    def retrain_model(self):
        report = self.kb_service.validate()
        if not report.is_valid:
            error(self, 'Нельзя обучить модель', 'Сначала заполните базу знаний полностью и устраните ошибки в разделе проверки полноты знаний.')
            return
        try:
            metrics = self.ml_service.train(self.kb_service.data)
        except Exception as exc:
            error(self, 'Ошибка обучения', str(exc))
            return
        self.refresh_status()
        info(
            self,
            'Обучение завершено',
            f"ML-модель успешно обучена.\nAccuracy: {metrics['accuracy']:.3f}\nMacro-F1: {metrics['macro_f1']:.3f}\nВсего синтетических образцов: {metrics['samples_total']}",
        )

    def reset_knowledge_base(self):
        self.kb_service.reset_to_defaults()
        self.refresh_status()
        info(self, 'База знаний восстановлена', 'Значения базы знаний снова соответствуют курсовой документации.')
