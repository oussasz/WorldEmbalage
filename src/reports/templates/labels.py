from __future__ import annotations
from reports.pdf_generator import PDFGenerator
from pathlib import Path


def build_labels_pdf(title: str, labels: list[str]) -> Path:
    gen = PDFGenerator()
    header = [title, 'Etiquettes:'] + [f" - {l}" for l in labels]
    return gen.simple_doc(f"Labels_{title}", header)

__all__ = ['build_labels_pdf']
