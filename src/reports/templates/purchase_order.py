from __future__ import annotations
from reports.pdf_generator import PDFGenerator
from pathlib import Path
from datetime import date


def build_purchase_order_pdf(reference: str, supplier_name: str, order_date: date, lines: list[dict]) -> Path:
    gen = PDFGenerator()
    rows: list[list[str]] = []
    for l in lines:
        rows.append([
            l['description'],
            str(l['quantity'])
        ])
    return gen.build_table_doc(
        f"Bon de Commande {reference} - {supplier_name} - {order_date.strftime('%d/%m/%Y')}",
        ['Description', 'Qté'],
        rows
    )

__all__ = ['build_purchase_order_pdf']
