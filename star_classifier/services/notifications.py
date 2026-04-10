"""Reusable dialog helpers."""

from __future__ import annotations

from tkinter import messagebox


def info(parent, title: str, text: str) -> None:
    messagebox.showinfo(title, text, parent=parent)


def warning(parent, title: str, text: str) -> None:
    messagebox.showwarning(title, text, parent=parent)


def error(parent, title: str, text: str) -> None:
    messagebox.showerror(title, text, parent=parent)
