"""ML model service adapted for the star luminosity classifier."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from star_classifier.utils.formatting import knowledge_signature


class MlClassifierService:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.models_dir = self.project_dir / 'models'
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.models_dir / 'star_luminosity_mlp.joblib'
        self.meta_path = self.models_dir / 'star_luminosity_mlp.meta.json'
        self.bundle = None
        self.error_message = ''
        self._load()

    def _load(self) -> None:
        self.bundle = None
        self.error_message = ''
        if not self.model_path.exists():
            self.error_message = 'ML-модель ещё не обучена.'
            return
        try:
            self.bundle = joblib.load(self.model_path)
        except Exception as exc:
            self.error_message = f'Не удалось загрузить ML-модель: {exc}'

    @property
    def is_ready(self) -> bool:
        return self.bundle is not None

    def read_metadata(self) -> dict:
        if not self.meta_path.exists():
            return {}
        return json.loads(self.meta_path.read_text(encoding='utf-8'))

    def is_compatible(self, knowledge_base: dict) -> bool:
        meta = self.read_metadata()
        return bool(meta) and meta.get('knowledge_signature') == knowledge_signature(knowledge_base) and self.is_ready

    def _feature_columns(self, knowledge_base: dict) -> list[str]:
        return list(knowledge_base['properties'])

    def _prepare_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        prepared = frame.copy()
        for column in prepared.columns:
            series = pd.to_numeric(prepared[column], errors='coerce')
            if column != 'Поверхностная гравитация':
                series = series.where(series > 0)
                prepared[column] = np.log10(series)
            else:
                prepared[column] = series
        return prepared

    def _sample_value(self, interval: dict, property_name: str, rng: np.random.Generator) -> float:
        low = float(interval['min'])
        high = float(interval['max'])
        if property_name != 'Поверхностная гравитация' and low > 0 and high / low >= 20:
            return float(10 ** rng.uniform(np.log10(low), np.log10(high)))
        return float(rng.uniform(low, high))

    def _mask_row(self, row: dict, properties: list[str], rng: np.random.Generator) -> dict:
        masked = dict(row)
        if len(properties) <= 1:
            return masked
        if rng.random() < 0.65:
            keep_count = int(rng.integers(1, len(properties) + 1))
            keep = set(rng.choice(properties, size=keep_count, replace=False).tolist())
            for property_name in properties:
                if property_name not in keep:
                    masked[property_name] = np.nan
        return masked

    def _build_dataset(self, knowledge_base: dict, n_per_class: int = 1200, random_state: int = 42) -> pd.DataFrame:
        rng = np.random.default_rng(random_state)
        properties = self._feature_columns(knowledge_base)
        rows = []
        for class_name in knowledge_base['classes']:
            description = knowledge_base['class_descriptions'].get(class_name, [])
            class_values = knowledge_base['class_values'].get(class_name, {})
            for _ in range(n_per_class):
                row = {}
                for property_name in properties:
                    if property_name in description and class_values.get(property_name) is not None:
                        interval = class_values[property_name]
                    else:
                        interval = knowledge_base['possible_values'].get(property_name)
                    if interval is None:
                        raise ValueError(f'Нельзя обучить модель: не заполнен диапазон для свойства «{property_name}».')
                    row[property_name] = self._sample_value(interval, property_name, rng)
                row = self._mask_row(row, properties, rng)
                row['target'] = class_name
                rows.append(row)

        sample_input = knowledge_base.get('sample_input') or {}
        sample_target_class = knowledge_base.get('sample_target_class')
        if sample_target_class in knowledge_base.get('classes', []) and sample_input:
            for _ in range(max(120, n_per_class // 3)):
                row = {}
                for property_name in properties:
                    value = sample_input.get(property_name)
                    if value is None:
                        row[property_name] = np.nan
                        continue
                    value = float(value)
                    if property_name != 'Поверхностная гравитация':
                        noise = max(abs(value) * 0.03, 1e-6)
                    else:
                        noise = 0.03
                    row[property_name] = float(rng.uniform(value - noise, value + noise))
                row = self._mask_row(row, properties, rng)
                row['target'] = sample_target_class
                rows.append(row)
        return pd.DataFrame(rows)

    def train(self, knowledge_base: dict, n_per_class: int = 1200, random_state: int = 42) -> dict:
        dataset = self._build_dataset(knowledge_base, n_per_class=n_per_class, random_state=random_state)
        feature_columns = self._feature_columns(knowledge_base)
        x = self._prepare_features(dataset[feature_columns])
        y = dataset['target']
        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=0.2,
            stratify=y,
            random_state=random_state,
        )
        encoder = LabelEncoder()
        y_train_encoded = encoder.fit_transform(y_train)
        y_test_encoded = encoder.transform(y_test)

        pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('model', MLPClassifier(
                hidden_layer_sizes=(128, 64),
                activation='relu',
                learning_rate_init=0.001,
                max_iter=1500,
                random_state=random_state,
                early_stopping=False,
            )),
        ])
        pipeline.fit(x_train, y_train_encoded)

        predictions_encoded = pipeline.predict(x_test)
        accuracy = float(accuracy_score(y_test_encoded, predictions_encoded))
        macro_f1 = float(f1_score(y_test_encoded, predictions_encoded, average='macro'))

        bundle = {
            'pipeline': pipeline,
            'encoder': encoder,
            'properties': feature_columns,
            'classes': list(knowledge_base['classes']),
        }
        joblib.dump(bundle, self.model_path)
        metadata = {
            'model_type': 'sklearn.neural_network.MLPClassifier',
            'knowledge_signature': knowledge_signature(knowledge_base),
            'accuracy': accuracy,
            'macro_f1': macro_f1,
            'n_per_class': n_per_class,
            'samples_total': int(len(dataset)),
            'supports_missing_inputs': True,
            'feature_space': 'log10 for positive astrophysical quantities + raw log g',
        }
        self.meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        self._load()
        return metadata

    def predict(self, inputs: dict[str, float], allowed_labels: list[str] | None = None, top_n: int = 7) -> tuple[str, list[tuple[str, float]]]:
        if not self.is_ready:
            raise RuntimeError(self.error_message or 'ML-модель недоступна.')
        feature_columns = self.bundle['properties']
        row = [{property_name: inputs.get(property_name, np.nan) for property_name in feature_columns}]
        sample = pd.DataFrame(row, columns=feature_columns)
        sample = self._prepare_features(sample)
        probabilities = self.bundle['pipeline'].predict_proba(sample)[0]
        encoded_classes = self.bundle['pipeline'].named_steps['model'].classes_
        classes = self.bundle['encoder'].inverse_transform(encoded_classes)
        scored = [(str(class_name), float(probability)) for class_name, probability in zip(classes, probabilities)]
        if allowed_labels is not None:
            allowed = set(allowed_labels)
            scored = [item for item in scored if item[0] in allowed]
            total = sum(probability for _, probability in scored)
            if total > 0:
                scored = [(class_name, probability / total) for class_name, probability in scored]
        if not scored:
            raise RuntimeError('ML-модель не смогла выбрать подходящий класс.')
        scored.sort(key=lambda item: item[1], reverse=True)
        predicted = scored[0][0]
        return predicted, scored[:top_n]
