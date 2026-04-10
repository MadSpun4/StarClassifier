"""Application theme."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter.font as tkfont

COLORS = {
    'bg': '#efefef',
    'panel': '#f7f7f7',
    'white': '#ffffff',
    'border': '#6b6b6b',
    'light_border': '#bcbcbc',
    'text': '#111111',
    'muted': '#555555',
    'red': '#ff5757',
    'green': '#8bc53f',
    'gray_btn': '#d9d9d9',
    'selected': '#cfcfcf',
    'blue': '#4f83ff',
}


@dataclass(frozen=True)
class UiFonts:
    base: tkfont.Font
    heading: tkfont.Font
    section: tkfont.Font
    small: tkfont.Font
    big: tkfont.Font
    launcher_heading: tkfont.Font
    launcher_text: tkfont.Font



def build_fonts() -> UiFonts:
    base = tkfont.nametofont('TkDefaultFont').copy()
    base.configure(family='Segoe UI', size=10)
    return UiFonts(
        base=base,
        heading=tkfont.Font(family='Segoe UI', size=15, weight='bold'),
        section=tkfont.Font(family='Segoe UI', size=12, weight='bold'),
        small=tkfont.Font(family='Segoe UI', size=9),
        big=tkfont.Font(family='Segoe UI', size=14, weight='bold'),
        launcher_heading=tkfont.Font(family='Segoe UI', size=16, weight='bold'),
        launcher_text=tkfont.Font(family='Segoe UI', size=10),
    )
