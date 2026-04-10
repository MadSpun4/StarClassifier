"""Reusable listbox wrapper."""

from __future__ import annotations

import tkinter as tk

from star_classifier.theme import COLORS


class ListboxPanel(tk.Frame):
    def __init__(self, master, *, items, font, width=None, height=None, selected_idx=0, bg=None):
        super().__init__(master, bg=bg or COLORS['bg'])
        self.listbox = tk.Listbox(
            self,
            width=width,
            height=height,
            exportselection=False,
            selectbackground=COLORS['selected'],
            relief='flat',
            highlightthickness=1,
            highlightbackground=COLORS['light_border'],
            activestyle='none',
            font=font,
        )
        self.scrollbar = tk.Scrollbar(self, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='left', fill='y')
        self.set_items(items, selected_idx)

    def set_items(self, items, selected_idx=0):
        self.listbox.delete(0, 'end')
        for item in items:
            self.listbox.insert('end', item)
        if items:
            index = max(0, min(selected_idx, len(items) - 1))
            self.listbox.selection_set(index)
            self.listbox.see(index)

    def current_value(self):
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.listbox.get(selection[0])
