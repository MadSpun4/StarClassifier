"""Train the star luminosity neural model from the current knowledge base."""

from __future__ import annotations

from pathlib import Path

from star_classifier.repositories.knowledge_base_repository import KnowledgeBaseRepository
from star_classifier.services.knowledge_base_service import KnowledgeBaseService
from star_classifier.services.ml_classifier import MlClassifierService


def main():
    project_dir = Path(__file__).resolve().parent
    repository = KnowledgeBaseRepository(project_dir)
    kb_service = KnowledgeBaseService(repository)
    ml_service = MlClassifierService(project_dir)
    report = kb_service.validate()
    if not report.is_valid:
        raise SystemExit('База знаний заполнена не полностью. Сначала исправьте ошибки в редакторе знаний.')
    metrics = ml_service.train(kb_service.data)
    print('Обучение завершено.')
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro-F1: {metrics['macro_f1']:.4f}")
    print(f"Всего образцов: {metrics['samples_total']}")


if __name__ == '__main__':
    main()
