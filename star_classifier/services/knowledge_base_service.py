"""Editable knowledge base service."""

from __future__ import annotations

from copy import deepcopy

from star_classifier.domain import ValidationReport
from star_classifier.repositories.knowledge_base_repository import KnowledgeBaseRepository
from star_classifier.utils.formatting import knowledge_signature


class KnowledgeBaseService:
    def __init__(self, repository: KnowledgeBaseRepository):
        self.repository = repository
        self._data = self.repository.load()

    @property
    def data(self) -> dict:
        return self._data

    @property
    def signature(self) -> str:
        return knowledge_signature(self._data)

    def reload(self) -> dict:
        self._data = self.repository.load()
        return self._data

    def reset_to_defaults(self) -> dict:
        self._data = self.repository.reset_to_defaults()
        return self._data

    def save(self) -> None:
        self.repository.save(self._data)

    def snapshot(self) -> dict:
        return deepcopy(self._data)

    def list_classes(self) -> list[str]:
        return list(self._data['classes'])

    def list_properties(self) -> list[str]:
        return list(self._data['properties'])

    def get_possible_range(self, property_name: str) -> dict | None:
        return self._data['possible_values'].get(property_name)

    def get_class_description(self, class_name: str) -> list[str]:
        return list(self._data['class_descriptions'].get(class_name, []))


    def get_class_range(self, class_name: str, property_name: str) -> dict | None:
        return self._data['class_values'].get(class_name, {}).get(property_name)

    def _assert_range_inside_possible(self, property_name: str, low: float, high: float) -> None:
        possible_range = self.get_possible_range(property_name)
        if possible_range is None:
            raise ValueError(
                f'Сначала задайте возможные значения для свойства «{property_name}».')
        possible_min = float(possible_range['min'])
        possible_max = float(possible_range['max'])
        if low < possible_min or high > possible_max:
            raise ValueError(
                f'Значение для класса светимости должно находиться в пределах возможных значений свойства: '
                f'[{possible_min}; {possible_max}].'
            )

    def _find_out_of_bounds_class_ranges_for_property(self, property_name: str, low: float, high: float) -> list[tuple[str, dict]]:
        invalid: list[tuple[str, dict]] = []
        for class_name in self._data['classes']:
            class_range = self._data['class_values'].get(class_name, {}).get(property_name)
            if class_range is None:
                continue
            class_min = float(class_range['min'])
            class_max = float(class_range['max'])
            if class_min < low or class_max > high:
                invalid.append((class_name, class_range))
        return invalid

    def add_class(self, class_name: str) -> None:
        name = class_name.strip()
        if not name:
            raise ValueError('Введите название класса светимости.')
        if name in self._data['classes']:
            raise ValueError('Такой класс светимости уже существует.')
        self._data['classes'].append(name)
        self._data['class_descriptions'][name] = []
        self._data['class_values'][name] = {}
        self.save()

    def delete_class(self, class_name: str) -> None:
        if class_name not in self._data['classes']:
            return
        self._data['classes'].remove(class_name)
        self._data['class_descriptions'].pop(class_name, None)
        self._data['class_values'].pop(class_name, None)
        self.save()

    def add_property(self, property_name: str) -> None:
        name = property_name.strip()
        if not name:
            raise ValueError('Введите название свойства звезды.')
        if name in self._data['properties']:
            raise ValueError('Такое свойство уже существует.')
        self._data['properties'].append(name)
        self._data['possible_values'][name] = None
        for class_name in self._data['classes']:
            self._data['class_values'].setdefault(class_name, {})
        self.save()

    def delete_property(self, property_name: str) -> None:
        if property_name not in self._data['properties']:
            return
        self._data['properties'].remove(property_name)
        self._data['possible_values'].pop(property_name, None)
        for class_name in self._data['classes']:
            description = self._data['class_descriptions'].setdefault(class_name, [])
            if property_name in description:
                description.remove(property_name)
            self._data['class_values'].setdefault(class_name, {}).pop(property_name, None)
        self.save()

    def validate_possible_range_candidate(self, property_name: str, low: float, high: float) -> None:
        if low > high:
            raise ValueError('Начальная граница не может быть больше конечной.')
        invalid_ranges = self._find_out_of_bounds_class_ranges_for_property(property_name, float(low), float(high))
        if invalid_ranges:
            details = ', '.join(
                f'{class_name} [{class_range["min"]}; {class_range["max"]}]'
                for class_name, class_range in invalid_ranges
            )
            raise ValueError(
                'Нельзя сохранить возможные значения свойства, потому что текущие значения классов выйдут за их пределы: '
                + details
            )

    def update_possible_range(self, property_name: str, low: float, high: float) -> None:
        self.validate_possible_range_candidate(property_name, low, high)
        self._data['possible_values'][property_name] = {'min': float(low), 'max': float(high)}
        self.save()

    def set_class_description(self, class_name: str, properties: list[str]) -> None:
        self._data['class_descriptions'][class_name] = [p for p in self._data['properties'] if p in properties]
        self.save()

    def validate_class_range_candidate(self, property_name: str, low: float, high: float) -> None:
        if low > high:
            raise ValueError('Начальная граница не может быть больше конечной.')
        self._assert_range_inside_possible(property_name, float(low), float(high))

    def update_class_range(self, class_name: str, property_name: str, low: float, high: float) -> None:
        self.validate_class_range_candidate(property_name, low, high)
        self._data['class_values'].setdefault(class_name, {})[property_name] = {
            'min': float(low),
            'max': float(high),
        }
        self.save()

    def set_sample_input(self, values: dict[str, float]) -> None:
        self._data['sample_input'] = {k: float(v) for k, v in values.items()}
        self.save()

    def validate(self) -> ValidationReport:
        report = ValidationReport()
        used_properties: set[str] = set()

        for property_name in self._data['properties']:
            if self._data['possible_values'].get(property_name) is None:
                report.missing_possible_values.append(property_name)

        for class_name in self._data['classes']:
            description = self._data['class_descriptions'].get(class_name, [])
            if not description:
                report.classes_without_description.append(class_name)
                continue
            used_properties.update(description)
            for property_name in description:
                class_range = self._data['class_values'].get(class_name, {}).get(property_name)
                if class_range is None:
                    report.class_properties_without_values.append((class_name, property_name))
                    continue
                possible_range = self._data['possible_values'].get(property_name)
                if possible_range is None:
                    continue
                class_min = float(class_range['min'])
                class_max = float(class_range['max'])
                possible_min = float(possible_range['min'])
                possible_max = float(possible_range['max'])
                if class_min < possible_min or class_max > possible_max:
                    report.class_ranges_out_of_possible_bounds.append(
                        (class_name, property_name, class_min, class_max, possible_min, possible_max)
                    )

        report.properties_not_used = [
            property_name for property_name in self._data['properties']
            if property_name not in used_properties
        ]
        return report
