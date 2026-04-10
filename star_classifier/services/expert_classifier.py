"""Rule-based classifier with optional ML ranking."""

from __future__ import annotations

from star_classifier.domain import ClassificationResult, RejectionReason
from star_classifier.services.ml_classifier import MlClassifierService


class ExpertClassifierService:
    def __init__(self, ml_service: MlClassifierService):
        self.ml_service = ml_service

    def classify(self, knowledge_base: dict, inputs: dict[str, float]) -> ClassificationResult:
        provided_properties = [property_name for property_name in knowledge_base['properties'] if property_name in inputs]
        if not provided_properties:
            return ClassificationResult(
                final_class=None,
                matched_classes=[],
                rejected=[],
                source='none',
                note='Не введено ни одного значения свойства звезды.',
                evaluated_properties=[],
            )

        matched: list[str] = []
        rejected: list[RejectionReason] = []

        for class_name in knowledge_base['classes']:
            description = knowledge_base['class_descriptions'].get(class_name, [])
            class_values = knowledge_base['class_values'].get(class_name, {})
            rejection = None
            for property_name in description:
                if property_name not in inputs:
                    continue
                interval = class_values.get(property_name)
                user_value = inputs[property_name]
                if interval is None:
                    rejection = RejectionReason(
                        class_name=class_name,
                        property_name=property_name,
                        input_value=user_value,
                        message='Знания об этом свойстве для класса не заполнены.',
                    )
                    break
                if not (interval['min'] <= user_value <= interval['max']):
                    rejection = RejectionReason(
                        class_name=class_name,
                        property_name=property_name,
                        input_value=user_value,
                        range_min=interval['min'],
                        range_max=interval['max'],
                    )
                    break
            if rejection is None:
                matched.append(class_name)
            else:
                rejected.append(rejection)

        final_class = matched[0] if len(matched) == 1 else None
        probabilities: list[tuple[str, float]] = []
        ml_note = ''

        if matched and self.ml_service.is_compatible(knowledge_base):
            allowed = matched if len(matched) > 1 else None
            _, probabilities = self.ml_service.predict(
                inputs,
                allowed_labels=allowed,
                top_n=len(matched) if len(matched) > 1 else len(knowledge_base['classes']),
            )
            if len(matched) > 1:
                ml_note = 'Ниже показаны вероятности ML-модели среди классов, не опровергнутых алгоритмом.'
            else:
                ml_note = 'Ниже показаны вероятности ML-модели по всем классам светимости.'
        elif matched:
            ml_note = 'ML-модель отсутствует или не соответствует текущей базе знаний.'

        if not matched:
            return ClassificationResult(
                final_class=None,
                matched_classes=[],
                rejected=rejected,
                source='none',
                note='Алгоритм не нашёл подходящих классов светимости по введённым данным.',
                evaluated_properties=provided_properties,
                ml_note=ml_note,
            )

        if len(matched) == 1:
            note = 'Алгоритм нашёл один подходящий класс светимости по методу опровержения гипотез.'
        else:
            note = (
                f'Алгоритм нашёл {len(matched)} возможных классов светимости. '
                'Это означает, что по введённым параметрам нельзя однозначно выбрать один класс только правилами базы знаний.'
            )

        matching_rows = []
        for property_name in provided_properties:
            matching_rows.append((property_name, str(inputs[property_name])))

        return ClassificationResult(
            final_class=final_class,
            matched_classes=matched,
            rejected=rejected,
            source='expert' if len(matched) == 1 else 'expert_multiple',
            matching_rows=matching_rows,
            probabilities=probabilities,
            note=note,
            evaluated_properties=provided_properties,
            ml_note=ml_note,
        )
