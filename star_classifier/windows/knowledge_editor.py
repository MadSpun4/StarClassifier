"""Functional knowledge editor window."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from star_classifier.services.notifications import error, info
from star_classifier.theme import COLORS
from star_classifier.utils.formatting import format_number, format_range, parse_float
from star_classifier.widgets.listbox_panel import ListboxPanel
from star_classifier.windows.base import BaseWindow


class KnowledgeEditorWindow(BaseWindow):
    def __init__(self, master, *, kb_service, ml_service, on_data_changed=None):
        super().__init__(master, 'Редактор базы знаний')
        self.kb_service = kb_service
        self.ml_service = ml_service
        self.on_data_changed = on_data_changed or (lambda: None)
        self.page_content = None
        self.current_page = 'classes'
        classes = self.kb_service.list_classes()
        properties = self.kb_service.list_properties()
        self.selected_class = tk.StringVar(value=classes[0] if classes else '')
        self.selected_property = tk.StringVar(value=properties[0] if properties else '')
        self.selected_possible_property = tk.StringVar(value=properties[0] if properties else '')
        self.nav_buttons = {}
        self.sidebar = tk.Frame(self.body, bg=COLORS['panel'], width=260, bd=1, relief='solid')
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        self.workspace = tk.Frame(self.body, bg=COLORS['bg'])
        self.workspace.pack(side='left', fill='both', expand=True)
        self._build_sidebar()
        self.show_page(self.current_page)

    def _build_sidebar(self):
        items = [
            ('classes', 'Классы светимости'),
            ('properties', 'Свойства звезды'),
            ('possible_values', 'Возможные значения свойств'),
            ('class_description', 'Описание свойств класса светимости'),
            ('class_value', 'Значения для класса светимости'),
            ('validation', 'Проверка полноты знаний'),
        ]
        for key, label in items:
            button = tk.Button(
                self.sidebar,
                text=label,
                anchor='w',
                padx=8,
                pady=8,
                bg=COLORS['white'] if key != 'validation' else '#dcdcdc',
                relief='solid',
                bd=1,
                font=self.fonts.small,
                cursor='hand2',
                command=lambda current=key: self.show_page(current),
            )
            if key == 'validation':
                button.pack(side='bottom', fill='x')
            else:
                button.pack(fill='x')
            self.nav_buttons[key] = button

    def show_page(self, key: str):
        self.current_page = key
        if self.page_content is not None:
            self.page_content.destroy()
        self.page_content = tk.Frame(self.workspace, bg=COLORS['bg'])
        self.page_content.pack(fill='both', expand=True)
        for name, button in self.nav_buttons.items():
            button.configure(bg='#d7d7d7' if name == key else COLORS['white'])
        if key == 'validation':
            self.nav_buttons[key].configure(bg='#bfbfbf')
        getattr(self, f'build_{key}_page')(self.page_content)

    def _after_change(self, message: str | None = None):
        self.kb_service.reload()
        self.on_data_changed()
        self.show_page(self.current_page)
        if message:
            info(self, 'Готово', message)

    def _remember_selected(self, panel, variable):
        value = panel.current_value()
        if value is not None:
            variable.set(value)
            self.show_page(self.current_page)

    def _set_entry_border(self, entry: tk.Entry, mode: str = 'normal'):
        palette = {
            'normal': COLORS['light_border'],
            'valid': '#4cae4f',
            'error': '#d9534f',
        }
        color = palette.get(mode, COLORS['light_border'])
        entry.configure(highlightthickness=2, highlightbackground=color, highlightcolor=color)

    def _build_range_editor(self, parent, *, current_range, initial_range, help_text: str, validator, save_command):
        grid = tk.Frame(parent, bg=COLORS['bg'])
        grid.pack(fill='x', pady=(2, 0))
        grid.grid_columnconfigure(0, minsize=110)
        grid.grid_columnconfigure(1, minsize=110)
        grid.grid_columnconfigure(2, minsize=30)
        grid.grid_columnconfigure(3, minsize=110)
        grid.grid_columnconfigure(4, minsize=110)

        tk.Label(grid, text='Текущее значение', bg=COLORS['bg'], font=self.fonts.small).grid(row=0, column=0, columnspan=2, sticky='w')
        tk.Label(grid, text='Новое значение', bg=COLORS['bg'], font=self.fonts.small).grid(row=0, column=3, columnspan=2, sticky='w')

        tk.Label(grid, text='От', bg=COLORS['bg'], font=self.fonts.base).grid(row=1, column=0, sticky='w', pady=(10, 0))
        tk.Label(grid, text='До', bg=COLORS['bg'], font=self.fonts.base).grid(row=1, column=1, sticky='w', pady=(10, 0))
        tk.Label(grid, text='От', bg=COLORS['bg'], font=self.fonts.base).grid(row=1, column=3, sticky='w', pady=(10, 0))
        tk.Label(grid, text='До', bg=COLORS['bg'], font=self.fonts.base).grid(row=1, column=4, sticky='w', pady=(10, 0))

        tk.Label(grid, text=format_number(current_range.get('min')), bg=COLORS['bg'], font=self.fonts.base).grid(row=2, column=0, sticky='w')
        tk.Label(grid, text=format_number(current_range.get('max')), bg=COLORS['bg'], font=self.fonts.base).grid(row=2, column=1, sticky='w')

        low_var = tk.StringVar(value='' if initial_range.get('min') is None else format_number(initial_range.get('min')))
        high_var = tk.StringVar(value='' if initial_range.get('max') is None else format_number(initial_range.get('max')))
        entry_low = tk.Entry(grid, relief='solid', bd=1, font=self.fonts.base, width=12, textvariable=low_var)
        entry_high = tk.Entry(grid, relief='solid', bd=1, font=self.fonts.base, width=12, textvariable=high_var)
        entry_low.grid(row=2, column=3, sticky='w', pady=6)
        entry_high.grid(row=2, column=4, sticky='w', pady=6)
        self._set_entry_border(entry_low, 'normal')
        self._set_entry_border(entry_high, 'normal')

        help_label = tk.Label(parent, text=help_text, bg=COLORS['bg'], fg=COLORS['muted'], font=self.fonts.small, wraplength=520, justify='left')
        help_label.pack(anchor='w', pady=(8, 2))
        status_label = tk.Label(parent, text='Введите новые границы диапазона. Ошибка будет подсвечена до сохранения.', bg=COLORS['bg'], fg=COLORS['muted'], font=self.fonts.small, wraplength=520, justify='left')
        status_label.pack(anchor='w')

        def refresh_validation(*_):
            low_text = low_var.get().strip()
            high_text = high_var.get().strip()
            if not low_text and not high_text:
                self._set_entry_border(entry_low, 'normal')
                self._set_entry_border(entry_high, 'normal')
                status_label.configure(text='Введите новые границы диапазона. Ошибка будет подсвечена до сохранения.', fg=COLORS['muted'])
                return

            low = high = None
            low_ok = True
            high_ok = True

            if low_text:
                try:
                    low = parse_float(low_text)
                except Exception:
                    low_ok = False
            if high_text:
                try:
                    high = parse_float(high_text)
                except Exception:
                    high_ok = False

            self._set_entry_border(entry_low, 'error' if not low_ok else 'normal')
            self._set_entry_border(entry_high, 'error' if not high_ok else 'normal')

            if not low_ok or not high_ok:
                status_label.configure(text='Границы диапазона должны быть корректными числами.', fg='#d9534f')
                return
            if low is None or high is None:
                status_label.configure(text='Заполните обе границы диапазона.', fg='#d9534f')
                return

            try:
                validator(low, high)
            except Exception as exc:
                self._set_entry_border(entry_low, 'error')
                self._set_entry_border(entry_high, 'error')
                status_label.configure(text=str(exc), fg='#d9534f')
                return

            self._set_entry_border(entry_low, 'valid')
            self._set_entry_border(entry_high, 'valid')
            status_label.configure(text='Диапазон корректен и может быть сохранён.', fg='#1f8d36')

        low_var.trace_add('write', refresh_validation)
        high_var.trace_add('write', refresh_validation)
        refresh_validation()

        actions = tk.Frame(parent, bg=COLORS['bg'])
        actions.pack(fill='x', pady=(14, 0))
        tk.Button(actions, text='Сохранить', bg=COLORS['green'], bd=0, padx=18, pady=8, cursor='hand2', command=lambda: save_command(low_var.get(), high_var.get())).pack(side='right')

    def build_classes_page(self, parent):
        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=18, pady=16)
        tk.Label(area, text='Классы светимости', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='w', pady=(0, 8))

        panel = ListboxPanel(area, items=self.kb_service.list_classes(), font=self.fonts.base, height=12)
        panel.pack(fill='both', expand=True)

        actions = tk.Frame(area, bg=COLORS['bg'])
        actions.pack(fill='x', pady=(12, 0))
        entry = tk.Entry(actions, relief='solid', bd=1, font=self.fonts.base)
        entry.pack(side='left', fill='x', expand=True, padx=(0, 10), ipady=5)
        tk.Button(actions, text='Добавить', bg=COLORS['green'], bd=0, padx=16, pady=8, cursor='hand2', command=lambda: self._add_class(entry)).pack(side='right')
        tk.Button(actions, text='Удалить выбранный', bg=COLORS['red'], fg='white', bd=0, padx=16, pady=8, cursor='hand2', command=lambda: self._delete_class(panel.current_value())).pack(side='right', padx=(0, 10))

    def _add_class(self, entry):
        try:
            self.kb_service.add_class(entry.get())
        except Exception as exc:
            error(self, 'Ошибка', str(exc))
            return
        self._after_change('Класс светимости добавлен.')

    def _delete_class(self, class_name):
        if not class_name:
            error(self, 'Ошибка', 'Сначала выберите класс светимости для удаления.')
            return
        if not messagebox.askyesno('Подтверждение', f'Удалить класс «{class_name}»?', parent=self):
            return
        self.kb_service.delete_class(class_name)
        self._after_change('Класс светимости удалён.')

    def build_properties_page(self, parent):
        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=18, pady=16)
        tk.Label(area, text='Свойства звезды', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='w', pady=(0, 8))

        panel = ListboxPanel(area, items=self.kb_service.list_properties(), font=self.fonts.base, height=12)
        panel.pack(fill='both', expand=True)

        actions = tk.Frame(area, bg=COLORS['bg'])
        actions.pack(fill='x', pady=(12, 0))
        entry = tk.Entry(actions, relief='solid', bd=1, font=self.fonts.base)
        entry.pack(side='left', fill='x', expand=True, padx=(0, 10), ipady=5)
        tk.Button(actions, text='Добавить', bg=COLORS['green'], bd=0, padx=16, pady=8, cursor='hand2', command=lambda: self._add_property(entry)).pack(side='right')
        tk.Button(actions, text='Удалить выбранное', bg=COLORS['red'], fg='white', bd=0, padx=16, pady=8, cursor='hand2', command=lambda: self._delete_property(panel.current_value())).pack(side='right', padx=(0, 10))

    def _add_property(self, entry):
        try:
            self.kb_service.add_property(entry.get())
        except Exception as exc:
            error(self, 'Ошибка', str(exc))
            return
        self._after_change('Свойство звезды добавлено.')

    def _delete_property(self, property_name):
        if not property_name:
            error(self, 'Ошибка', 'Сначала выберите свойство для удаления.')
            return
        if not messagebox.askyesno('Подтверждение', f'Удалить свойство «{property_name}»?', parent=self):
            return
        self.kb_service.delete_property(property_name)
        self._after_change('Свойство удалено.')

    def build_possible_values_page(self, parent):
        properties = self.kb_service.list_properties()
        if self.selected_possible_property.get() not in properties and properties:
            self.selected_possible_property.set(properties[0])

        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=14, pady=10)
        header = tk.Frame(area, bg=COLORS['bg'])
        header.pack(fill='x', pady=(0, 8))
        tk.Label(header, text='Свойства звезды', font=self.fonts.heading, bg=COLORS['bg']).pack(side='left')
        tk.Label(header, text='Значения', font=self.fonts.heading, bg=COLORS['bg']).pack(side='right', padx=(0, 190))

        content = tk.Frame(area, bg=COLORS['bg'])
        content.pack(fill='both', expand=True)
        left_panel = ListboxPanel(
            content,
            items=properties,
            font=self.fonts.base,
            width=34,
            height=12,
            selected_idx=properties.index(self.selected_possible_property.get()) if properties else 0,
        )
        left_panel.pack(side='left', fill='y', padx=(0, 24))
        left_panel.listbox.bind('<<ListboxSelect>>', lambda *_: self._remember_selected(left_panel, self.selected_possible_property))

        right = tk.Frame(content, bg=COLORS['bg'])
        right.pack(side='left', fill='both', expand=True)
        selected_property = self.selected_possible_property.get()
        current_range = self.kb_service.get_possible_range(selected_property) or {'min': None, 'max': None}
        help_text = 'Новое значение свойства не должно делать уже заданные диапазоны классов некорректными.'
        self._build_range_editor(
            right,
            current_range=current_range,
            initial_range=current_range,
            help_text=help_text,
            validator=lambda low, high: self.kb_service.validate_possible_range_candidate(selected_property, low, high),
            save_command=self._save_possible_value,
        )

    def _save_possible_value(self, low_text, high_text):
        try:
            low = parse_float(low_text)
            high = parse_float(high_text)
            self.kb_service.update_possible_range(self.selected_possible_property.get(), low, high)
        except Exception as exc:
            error(self, 'Ошибка', str(exc))
            return
        self._after_change('Возможные значения свойства сохранены.')

    def build_class_description_page(self, parent):
        classes = self.kb_service.list_classes()
        properties = self.kb_service.list_properties()
        if self.selected_class.get() not in classes and classes:
            self.selected_class.set(classes[0])
        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=14, pady=10)

        header = tk.Frame(area, bg=COLORS['bg'])
        header.pack(fill='x', pady=(0, 10))
        tk.Label(header, text='Классы светимости', font=self.fonts.heading, bg=COLORS['bg']).pack(side='left', padx=(0, 78))
        tk.Label(header, text='Свойства звезды', font=self.fonts.heading, bg=COLORS['bg']).pack(side='left')

        content = tk.Frame(area, bg=COLORS['bg'])
        content.pack(fill='both', expand=True)
        class_panel = ListboxPanel(content, items=classes, font=self.fonts.base, width=34, height=12, selected_idx=classes.index(self.selected_class.get()) if classes else 0)
        class_panel.pack(side='left', fill='y', padx=(0, 30))
        class_panel.listbox.bind('<<ListboxSelect>>', lambda *_: self._remember_selected(class_panel, self.selected_class))

        right = tk.Frame(content, bg=COLORS['bg'])
        right.pack(side='left', fill='both', expand=True)
        current = set(self.kb_service.get_class_description(self.selected_class.get()))
        select_all_var = tk.IntVar(value=1 if current and len(current) == len(properties) else 0)
        vars_map = {}

        def on_select_all():
            value = bool(select_all_var.get())
            for var in vars_map.values():
                var.set(1 if value else 0)

        top_right = tk.Frame(right, bg=COLORS['bg'])
        top_right.pack(fill='x')
        tk.Label(top_right, text='Выбрать все', bg=COLORS['bg'], font=self.fonts.small).pack(side='left', padx=(0, 12))
        tk.Checkbutton(top_right, variable=select_all_var, bg=COLORS['bg'], activebackground=COLORS['bg'], command=on_select_all).pack(side='left')

        for property_name in properties:
            row = tk.Frame(right, bg=COLORS['bg'])
            row.pack(fill='x', pady=10)
            tk.Label(row, text=property_name, bg=COLORS['bg'], anchor='w', font=self.fonts.base).pack(side='left', fill='x', expand=True)
            var = tk.IntVar(value=1 if property_name in current else 0)
            vars_map[property_name] = var
            tk.Checkbutton(row, variable=var, bg=COLORS['bg'], activebackground=COLORS['bg']).pack(side='right')

        actions = tk.Frame(area, bg=COLORS['bg'])
        actions.pack(fill='x')
        tk.Button(actions, text='Сохранить', bg=COLORS['green'], bd=0, padx=18, pady=8, cursor='hand2', command=lambda: self._save_class_description(vars_map)).pack(side='right')

    def _save_class_description(self, vars_map):
        selected = [name for name, var in vars_map.items() if var.get()]
        self.kb_service.set_class_description(self.selected_class.get(), selected)
        self._after_change('Описание свойств класса светимости сохранено.')

    def build_class_value_page(self, parent):
        classes = self.kb_service.list_classes()
        properties = self.kb_service.list_properties()
        if self.selected_class.get() not in classes and classes:
            self.selected_class.set(classes[0])
        if self.selected_property.get() not in properties and properties:
            self.selected_property.set(properties[0])

        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=14, pady=10)
        header = tk.Frame(area, bg=COLORS['bg'])
        header.pack(fill='x', pady=(0, 10))
        tk.Label(header, text='Классы светимости', font=self.fonts.heading, bg=COLORS['bg']).pack(side='left', padx=(0, 60))
        tk.Label(header, text='Свойства звезды', font=self.fonts.heading, bg=COLORS['bg']).pack(side='left', padx=(0, 70))
        tk.Label(header, text='Значения', font=self.fonts.heading, bg=COLORS['bg']).pack(side='left')

        content = tk.Frame(area, bg=COLORS['bg'])
        content.pack(fill='both', expand=True)
        class_panel = ListboxPanel(content, items=classes, font=self.fonts.base, width=30, height=12, selected_idx=classes.index(self.selected_class.get()) if classes else 0)
        class_panel.pack(side='left', fill='y', padx=(0, 18))
        class_panel.listbox.bind('<<ListboxSelect>>', lambda *_: self._remember_selected(class_panel, self.selected_class))

        property_panel = ListboxPanel(content, items=properties, font=self.fonts.base, width=30, height=12, selected_idx=properties.index(self.selected_property.get()) if properties else 0)
        property_panel.pack(side='left', fill='y', padx=(0, 18))
        property_panel.listbox.bind('<<ListboxSelect>>', lambda *_: self._remember_selected(property_panel, self.selected_property))

        right = tk.Frame(content, bg=COLORS['bg'])
        right.pack(side='left', fill='both', expand=True)
        current_class = self.selected_class.get()
        current_property = self.selected_property.get()
        class_description = set(self.kb_service.get_class_description(current_class))
        property_is_allowed = current_property in class_description

        if not property_is_allowed:
            possible_range = self.kb_service.get_possible_range(current_property) or {'min': None, 'max': None}
            tk.Label(
                right,
                text='Сначала добавьте это свойство в описание свойств выбранного класса светимости. Пока оно не входит в описание класса, задавать для него диапазон нельзя.',
                bg=COLORS['bg'],
                fg='#d9534f',
                font=self.fonts.small,
                wraplength=520,
                justify='left',
            ).pack(anchor='w', pady=(0, 10))
            tk.Label(
                right,
                text=f'Возможные значения свойства: {format_range(possible_range.get("min"), possible_range.get("max"))}.',
                bg=COLORS['bg'],
                fg=COLORS['muted'],
                font=self.fonts.small,
                wraplength=520,
                justify='left',
            ).pack(anchor='w')
            preview = tk.Frame(right, bg=COLORS['bg'])
            preview.pack(anchor='w', pady=(14, 0))
            tk.Label(preview, text='Текущее значение:', bg=COLORS['bg'], font=self.fonts.small).grid(row=0, column=0, columnspan=2, sticky='w')
            current_range = self.kb_service.get_class_range(current_class, current_property) or {'min': None, 'max': None}
            tk.Label(preview, text='От', bg=COLORS['bg'], font=self.fonts.base).grid(row=1, column=0, sticky='w', pady=(8, 0))
            tk.Label(preview, text='До', bg=COLORS['bg'], font=self.fonts.base).grid(row=1, column=1, sticky='w', padx=(24, 0), pady=(8, 0))
            tk.Label(preview, text=format_number(current_range.get('min')), bg=COLORS['bg'], font=self.fonts.base).grid(row=2, column=0, sticky='w')
            tk.Label(preview, text=format_number(current_range.get('max')), bg=COLORS['bg'], font=self.fonts.base).grid(row=2, column=1, sticky='w', padx=(24, 0))
            actions = tk.Frame(right, bg=COLORS['bg'])
            actions.pack(fill='x', pady=(14, 0))
            tk.Button(
                actions,
                text='Перейти к описанию свойств класса',
                bg=COLORS['gray_btn'],
                bd=0,
                padx=16,
                pady=8,
                cursor='hand2',
                command=lambda: self.show_page('class_description'),
            ).pack(side='left')
        else:
            current_range = self.kb_service.get_class_range(current_class, current_property) or {'min': None, 'max': None}
            possible_range = self.kb_service.get_possible_range(current_property) or {'min': None, 'max': None}
            help_text = f'Возможные значения свойства: {format_range(possible_range.get("min"), possible_range.get("max"))}. Значение класса должно лежать внутри этих границ.'
            initial_range = current_range if current_range.get('min') is not None or current_range.get('max') is not None else {'min': None, 'max': None}
            self._build_range_editor(
                right,
                current_range=current_range,
                initial_range=initial_range,
                help_text=help_text,
                validator=lambda low, high: self.kb_service.validate_class_range_candidate(self.selected_class.get(), self.selected_property.get(), low, high),
                save_command=self._save_class_value,
            )

    def _save_class_value(self, low_text, high_text):
        try:
            low = parse_float(low_text)
            high = parse_float(high_text)
            self.kb_service.update_class_range(self.selected_class.get(), self.selected_property.get(), low, high)
        except Exception as exc:
            error(self, 'Ошибка', str(exc))
            return
        self._after_change('Значение для класса светимости сохранено.')

    def build_validation_page(self, parent):
        report = self.kb_service.validate()
        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=14, pady=10)
        if report.is_valid:
            tk.Label(area, text='База знаний заполнена полностью.', fg='#1f8d36', bg=COLORS['bg'], font=self.fonts.section).pack(anchor='w', pady=(0, 14))
        else:
            tk.Label(area, text='В базе знаний имеются незаполненные поля.', fg='#dd2222', bg=COLORS['bg'], font=self.fonts.section).pack(anchor='w', pady=(0, 14))

        text = tk.Text(area, wrap='word', relief='solid', bd=1, font=self.fonts.small, height=18)
        text.pack(fill='both', expand=True)
        lines = []
        if report.missing_possible_values:
            lines.append('Возможные значения свойств:')
            for property_name in report.missing_possible_values:
                lines.append(f'  • {property_name}')
            lines.append('')
        if report.classes_without_description:
            lines.append('Описание свойств класса светимости:')
            for class_name in report.classes_without_description:
                lines.append(f'  • {class_name}')
            lines.append('')
        if report.class_properties_without_values:
            lines.append('Значения для класса светимости:')
            for class_name, property_name in report.class_properties_without_values:
                lines.append(f'  • {class_name} / {property_name}')
            lines.append('')
        if report.class_ranges_out_of_possible_bounds:
            lines.append('Значения классов, выходящие за пределы возможных значений свойств:')
            for class_name, property_name, class_min, class_max, possible_min, possible_max in report.class_ranges_out_of_possible_bounds:
                lines.append(
                    f'  • {class_name} / {property_name}: [{format_number(class_min)}; {format_number(class_max)}] вне [{format_number(possible_min)}; {format_number(possible_max)}]'
                )
            lines.append('')
        if report.class_values_outside_description:
            lines.append('Значения классов, заданные для свойств вне описания класса:')
            for class_name, property_name in report.class_values_outside_description:
                lines.append(f'  • {class_name} / {property_name}')
            lines.append('')
        if report.properties_not_used:
            lines.append('Свойства, которые пока не используются ни в одном описании класса:')
            for property_name in report.properties_not_used:
                lines.append(f'  • {property_name}')
        if not lines:
            lines.append('Ошибок не найдено.')
        text.insert('1.0', '\n'.join(lines))
        text.configure(state='disabled')

        bottom = tk.Frame(area, bg=COLORS['bg'])
        bottom.pack(fill='x', pady=(14, 0))
        tk.Button(bottom, text='Сбросить к начальным значениям', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self._reset_defaults).pack(side='left')
        tk.Button(bottom, text='Переобучить ML-модель', bg=COLORS['blue'], fg='white', bd=0, padx=16, pady=8, cursor='hand2', command=self._retrain_model).pack(side='right')

    def _reset_defaults(self):
        if not messagebox.askyesno('Подтверждение', 'Сбросить текущую базу знаний к стандартным значениям?', parent=self):
            return
        self.kb_service.reset_to_defaults()
        self.ml_service._load()
        self._after_change('База знаний восстановлена.')

    def _retrain_model(self):
        report = self.kb_service.validate()
        if not report.is_valid:
            error(self, 'Ошибка', 'Сначала заполните базу знаний полностью.')
            return
        try:
            metrics = self.ml_service.train(self.kb_service.data)
        except Exception as exc:
            error(self, 'Ошибка обучения', str(exc))
            return
        self.on_data_changed()
        info(self, 'Обучение завершено', f"Accuracy: {metrics['accuracy']:.3f}\nMacro-F1: {metrics['macro_f1']:.3f}")
        self.show_page(self.current_page)
