"""Base window."""

from __future__ import annotations

import tkinter as tk

from star_classifier.theme import COLORS, build_fonts


class BaseWindow(tk.Toplevel):
    def __init__(self, master, title: str, width: int = 1120, height: int = 680):
        super().__init__(master)
        self.title(title)
        self.geometry(f'{width}x{height}')
        self.minsize(width, height)
        self.configure(bg=COLORS['bg'])
        self.fonts = getattr(master, 'fonts', build_fonts())
        self.container = tk.Frame(self, bg=COLORS['bg'], bd=1, relief='solid')
        self.container.pack(fill='both', expand=True, padx=8, pady=8)
        self.body = tk.Frame(self.container, bg=COLORS['bg'])
        self.body.pack(fill='both', expand=True)
