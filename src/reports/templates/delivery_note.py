from __future__ import annotations
from reports.pdf_generator import PDFGenerator
from pathlib import Path
from datetime import date


def build_delivery_note_pdf(reference: str, client_name: str, delivery_date: date, lines: list[dict]) -> Path:
    gen = PDFGenerator()
    rows: list[list[str]] = []
    for l in lines:
        rows.append([
            l['description'],
            str(l['quantity'])
        ])
    return gen.build_table_doc(
        f"BL {reference} - {client_name} - {delivery_date.strftime('%d/%m/%Y')}",
        ['Description', 'Qté'],
        rows
    )

__all__ = ['build_delivery_note_pdf']
