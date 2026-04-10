"""Input, result, and knowledge base viewing window."""

from __future__ import annotations

import tkinter as tk

from star_classifier.services.notifications import error, info
from star_classifier.theme import COLORS
from star_classifier.utils.formatting import format_number, format_range, parse_float
from star_classifier.widgets.listbox_panel import ListboxPanel
from star_classifier.windows.base import BaseWindow


class DataEntryWindow(BaseWindow):
    def __init__(self, master, *, kb_service, expert_classifier, ml_service, on_data_changed=None):
        super().__init__(master, 'Ввод исходных данных')
        self.kb_service = kb_service
        self.expert_classifier = expert_classifier
        self.ml_service = ml_service
        self.on_data_changed = on_data_changed or (lambda: None)
        self.page_content = None
        self.current_inputs = {}
        self.current_property = tk.StringVar(value=self.kb_service.list_properties()[0])
        self.selected_view_class = tk.StringVar(value=self.kb_service.list_classes()[0])
        self.selected_view_property = tk.StringVar(value=self.kb_service.list_properties()[0])
        self.last_result = None
        self.show_input_page()

    def _clear_page(self):
        if self.page_content is not None:
            self.page_content.destroy()
        self.page_content = tk.Frame(self.body, bg=COLORS['bg'])
        self.page_content.pack(fill='both', expand=True)

    def show_input_page(self):
        self.title('Ввод исходных данных')
        self._clear_page()
        self.build_input_page(self.page_content)

    def show_result_page(self, result=None):
        if result is not None:
            self.last_result = result
        self.title('Классификация светимости звезды')
        self._clear_page()
        self.build_result_page(self.page_content)

    def show_knowledge_view_page(self):
        self.title('База знаний')
        self._clear_page()
        self.build_knowledge_view_page(self.page_content)

    def build_input_page(self, parent):
        properties = self.kb_service.list_properties()
        if self.current_property.get() not in properties and properties:
            self.current_property.set(properties[0])

        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=14, pady=10)

        content = tk.Frame(area, bg=COLORS['bg'])
        content.pack(fill='both', expand=True)

        left = tk.Frame(content, bg=COLORS['bg'])
        left.pack(side='left', fill='both', expand=True)
        middle = tk.Frame(content, bg=COLORS['bg'], width=260)
        middle.pack(side='left', fill='y', padx=20)
        middle.pack_propagate(False)
        right = tk.Frame(content, bg=COLORS['bg'])
        right.pack(side='left', fill='both', expand=True)

        tk.Label(left, text='Свойства звезды', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='center', pady=(0, 10))
        property_panel = ListboxPanel(left, items=properties, font=self.fonts.base, selected_idx=properties.index(self.current_property.get()) if properties else 0)
        property_panel.pack(fill='both', expand=True)
        property_panel.listbox.bind('<<ListboxSelect>>', lambda *_: self._on_input_property_selected(property_panel))

        tk.Label(middle, text='Значение', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='center', pady=(0, 10))
        value_entry = tk.Entry(middle, relief='solid', bd=1, justify='center', font=self.fonts.base)
        if self.current_property.get() in self.current_inputs:
            value_entry.insert(0, format_number(self.current_inputs[self.current_property.get()]))
        value_entry.pack(pady=(20, 10), ipady=6)
        tk.Button(middle, text='Сохранить значение', bg=COLORS['green'], bd=0, padx=16, pady=8, cursor='hand2', command=lambda: self._save_input_value(value_entry.get())).pack(fill='x')
        tk.Button(middle, text='Очистить значение свойства', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self._clear_current_property_value).pack(fill='x', pady=(10, 0))
        tk.Button(middle, text='Подставить параметры Солнца', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self._fill_solar_inputs).pack(fill='x', pady=(10, 0))
        tk.Button(middle, text='Подставить параметры Сириуса', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self._fill_sirius_inputs).pack(fill='x', pady=(10, 0))
        tk.Button(middle, text='Очистить все введённые значения', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self._clear_all_inputs).pack(fill='x', pady=(10, 0))

        tk.Label(right, text='Значения свойств', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='center', pady=(0, 10))
        summary_items = []
        for property_name in properties:
            summary_items.append(f'{property_name}   {format_number(self.current_inputs.get(property_name))}')
        summary_panel = ListboxPanel(right, items=summary_items, font=self.fonts.base, selected_idx=0)
        summary_panel.pack(fill='both', expand=True)

        hint = (
            'Можно вводить не все параметры. Алгоритм покажет все классы, которые не опровергаются '
            'введёнными значениями, а затем будут показаны вероятности ML-модели.'
        )
        tk.Label(area, text=hint, bg=COLORS['bg'], fg=COLORS['muted'], font=self.fonts.small, wraplength=900, justify='left').pack(fill='x', pady=(12, 0))

        bottom = tk.Frame(area, bg=COLORS['bg'])
        bottom.pack(fill='x', pady=(14, 0))
        tk.Button(bottom, text='Просмотр базы знаний', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self.show_knowledge_view_page).pack(side='left')
        tk.Button(bottom, text='Определить класс светимости', bg=COLORS['green'], bd=0, padx=16, pady=8, cursor='hand2', command=self._detect).pack(side='right')

    def _on_input_property_selected(self, panel):
        value = panel.current_value()
        if value is not None:
            self.current_property.set(value)
            self.show_input_page()

    def _save_input_value(self, text):
        if not text.strip():
            self.current_inputs.pop(self.current_property.get(), None)
            self.show_input_page()
            return
        try:
            value = parse_float(text)
        except Exception:
            error(self, 'Ошибка', 'Введите корректное числовое значение.')
            return
        self.current_inputs[self.current_property.get()] = value
        self.show_input_page()

    def _clear_current_property_value(self):
        self.current_inputs.pop(self.current_property.get(), None)
        self.show_input_page()

    def _clear_all_inputs(self):
        self.current_inputs = {}
        self.show_input_page()

    def _fill_solar_inputs(self):
        preset_inputs = self.kb_service.data.get('preset_inputs', {})
        solar_preset = preset_inputs.get('sun', {}).get('values')
        if solar_preset:
            self.current_inputs = dict(solar_preset)
        else:
            self.current_inputs = dict(self.kb_service.data.get('sample_input', {}))
        self.show_input_page()

    def _fill_sirius_inputs(self):
        preset_inputs = self.kb_service.data.get('preset_inputs', {})
        sirius_preset = preset_inputs.get('sirius', {}).get('values')
        if sirius_preset:
            self.current_inputs = dict(sirius_preset)
        else:
            self.current_inputs = {
                'Эффективная температура': 9940.0,
                'Поверхностная гравитация': 4.33,
                'Абсолютная светимость': 25.4,
                'Радиус звезды': 1.7,
            }
        self.show_input_page()

    def _detect(self):
        validation = self.kb_service.validate()
        if not validation.is_valid:
            error(self, 'Ошибка', 'База знаний заполнена не полностью. Сначала исправьте её в редакторе знаний.')
            return
        if not self.current_inputs:
            error(self, 'Недостаточно данных', 'Введите хотя бы одно значение свойства звезды.')
            return
        try:
            result = self.expert_classifier.classify(self.kb_service.data, self.current_inputs)
        except Exception as exc:
            error(self, 'Ошибка классификации', str(exc))
            return
        self.show_result_page(result)
        self.on_data_changed()

    def build_result_page(self, parent):
        result = self.last_result
        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=14, pady=10)
        if result is None:
            info(self, 'Нет данных', 'Результат классификации пока не рассчитан.')
            self.show_input_page()
            return

        panels = tk.Frame(area, bg=COLORS['bg'])
        panels.pack(fill='both', expand=True)
        left = tk.Frame(panels, bg=COLORS['white'], bd=1, relief='solid')
        left.pack(side='left', fill='both', expand=True, padx=(0, 12))
        right = tk.Frame(panels, bg=COLORS['white'], bd=1, relief='solid')
        right.pack(side='left', fill='both', expand=True)

        header_color = COLORS['green'] if result.matched_classes else COLORS['red']
        left_header = tk.Frame(left, bg=header_color, height=38)
        left_header.pack(fill='x')
        left_header.pack_propagate(False)
        tk.Label(left_header, text='Решение алгоритма', bg=header_color, font=self.fonts.big).pack(expand=True)

        if result.final_class:
            result_text = f'Подходящий класс светимости: {result.final_class}'
        elif result.matched_classes:
            result_text = 'Алгоритм нашёл несколько возможных классов светимости'
        else:
            result_text = 'Класс светимости не определён'

        tk.Label(left, text=result_text, bg=COLORS['white'], anchor='w', padx=12, pady=10, font=self.fonts.base, wraplength=430, justify='left').pack(fill='x')
        tk.Label(left, text=result.note, bg=COLORS['white'], anchor='w', justify='left', wraplength=430, padx=12, font=self.fonts.small).pack(fill='x', pady=(0, 10))

        tk.Label(left, text='Введённые значения', bg=COLORS['white'], font=self.fonts.section).pack(pady=(6, 10))
        table = tk.Frame(left, bg=COLORS['white'])
        table.pack(fill='x', padx=12)
        for property_name in result.evaluated_properties:
            row = tk.Frame(table, bg=COLORS['white'])
            row.pack(fill='x', pady=6)
            tk.Label(row, text=property_name, bg=COLORS['white'], anchor='w', width=28, font=self.fonts.small).pack(side='left')
            tk.Label(row, text=format_number(self.current_inputs.get(property_name)), bg=COLORS['white'], anchor='w', font=self.fonts.small).pack(side='left', fill='x', expand=True)
        if not result.evaluated_properties:
            tk.Label(table, text='Значения не введены.', bg=COLORS['white'], anchor='w', font=self.fonts.small).pack(fill='x')

        if result.matched_classes:
            tk.Label(left, text='Классы, не опровергнутые алгоритмом', bg=COLORS['white'], font=self.fonts.section).pack(pady=(14, 10))
            matched_box = tk.Frame(left, bg=COLORS['white'])
            matched_box.pack(fill='x', padx=12)
            for class_name in result.matched_classes:
                tk.Label(matched_box, text=f'• {class_name}', bg=COLORS['white'], anchor='w', font=self.fonts.small).pack(fill='x', pady=2)

        right_header = tk.Frame(right, bg=COLORS['red'], height=38)
        right_header.pack(fill='x')
        right_header.pack_propagate(False)
        tk.Label(right_header, text='Объяснение и вероятности', bg=COLORS['red'], font=self.fonts.big).pack(expand=True)

        text = tk.Text(right, wrap='word', relief='flat', bd=0, padx=12, pady=12, font=self.fonts.small)
        text.pack(fill='both', expand=True)
        lines = []
        if result.evaluated_properties:
            lines.append('Алгоритм учитывал только введённые свойства:')
            for property_name in result.evaluated_properties:
                lines.append(f'• {property_name}: {format_number(self.current_inputs[property_name])}')
            lines.append('')
        if result.probabilities:
            lines.append('Оценка ML-модели:')
            if result.ml_note:
                lines.append(result.ml_note)
            for class_name, probability in result.probabilities:
                lines.append(f'• {class_name}: {probability * 100:.2f}%')
            lines.append('')
        elif result.ml_note:
            lines.append(result.ml_note)
            lines.append('')
        if result.rejected:
            lines.append('Классы, опровергнутые алгоритмом:')
            for item in result.rejected:
                if item.message:
                    lines.append(f'• {item.message}')
                else:
                    lines.append(
                        f'• Класс светимости «{item.class_name}» опровергнут, так как значение {format_number(item.input_value)} свойства «{item.property_name}» не принадлежит множеству значений {format_range(item.range_min, item.range_max)}.'
                    )
        if not lines:
            lines.append('Объяснение отсутствует.')
        text.insert('1.0', '\n'.join(lines))
        text.configure(state='disabled')

        bottom = tk.Frame(area, bg=COLORS['bg'])
        bottom.pack(fill='x', pady=(14, 0))
        tk.Button(bottom, text='Вернуться к вводу исходных данных', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self.show_input_page).pack(anchor='center')

    def build_knowledge_view_page(self, parent):
        classes = self.kb_service.list_classes()
        properties = self.kb_service.list_properties()
        if self.selected_view_class.get() not in classes and classes:
            self.selected_view_class.set(classes[0])
        if self.selected_view_property.get() not in properties and properties:
            self.selected_view_property.set(properties[0])
        area = tk.Frame(parent, bg=COLORS['bg'])
        area.pack(fill='both', expand=True, padx=14, pady=10)
        content = tk.Frame(area, bg=COLORS['bg'])
        content.pack(fill='both', expand=True)
        column_1 = tk.Frame(content, bg=COLORS['bg'])
        column_1.pack(side='left', fill='both', expand=True, padx=(0, 12))
        column_2 = tk.Frame(content, bg=COLORS['bg'])
        column_2.pack(side='left', fill='both', expand=True, padx=(0, 12))
        column_3 = tk.Frame(content, bg=COLORS['bg'])
        column_3.pack(side='left', fill='both', expand=True)

        tk.Label(column_1, text='Классы светимости', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='center', pady=(0, 10))
        class_panel = ListboxPanel(column_1, items=classes, font=self.fonts.base, selected_idx=classes.index(self.selected_view_class.get()) if classes else 0)
        class_panel.pack(fill='both', expand=True)
        class_panel.listbox.bind('<<ListboxSelect>>', lambda *_: self._on_view_class_selected(class_panel))

        tk.Label(column_2, text='Свойства звезды', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='center', pady=(0, 10))
        property_panel = ListboxPanel(column_2, items=properties, font=self.fonts.base, selected_idx=properties.index(self.selected_view_property.get()) if properties else 0)
        property_panel.pack(fill='both', expand=True)
        property_panel.listbox.bind('<<ListboxSelect>>', lambda *_: self._on_view_property_selected(property_panel))

        tk.Label(column_3, text='Значения', font=self.fonts.heading, bg=COLORS['bg']).pack(anchor='center', pady=(0, 10))
        value_frame = tk.Frame(column_3, bg=COLORS['white'], highlightthickness=1, highlightbackground=COLORS['light_border'])
        value_frame.pack(fill='both', expand=True)
        interval = self.kb_service.get_class_range(self.selected_view_class.get(), self.selected_view_property.get())
        if interval is None:
            text = 'Для выбранной пары класс/свойство значение не задано.'
        else:
            text = f'От    {format_number(interval["min"])}      До    {format_number(interval["max"])}'
        tk.Label(value_frame, text=text, bg=COLORS['white'], font=self.fonts.section, wraplength=260, justify='center').pack(anchor='center', pady=20)

        bottom = tk.Frame(area, bg=COLORS['bg'])
        bottom.pack(fill='x', pady=(14, 0))
        tk.Button(bottom, text='Вернуться к вводу исходных данных', bg=COLORS['gray_btn'], bd=0, padx=16, pady=8, cursor='hand2', command=self.show_input_page).pack(anchor='center')

    def _on_view_class_selected(self, panel):
        value = panel.current_value()
        if value is not None:
            self.selected_view_class.set(value)
            self.show_knowledge_view_page()

    def _on_view_property_selected(self, panel):
        value = panel.current_value()
        if value is not None:
            self.selected_view_property.set(value)
            self.show_knowledge_view_page()
