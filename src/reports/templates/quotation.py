from __future__ import annotations
from reports.pdf_generator import PDFGenerator
from pathlib import Path
from datetime import date
from decimal import Decimal


def build_quotation_pdf(reference: str, client_name: str, issue_date: date, valid_until: date | None, items: list[dict], currency: str = 'EUR') -> Path:
    gen = PDFGenerator()
    total = Decimal('0')
    rows: list[list[str]] = []
    for it in items:
        line_total = Decimal(str(it['unit_price'])) * it['quantity']
        total += line_total
        rows.append([
            it['description'],
            str(it['quantity']),
            f"{it['unit_price']}",
            f"{line_total}" ,
        ])
    rows.append(['', '', 'TOTAL', f"{total} {currency}"])
    return gen.build_table_doc(
        f"Devis {reference}",
        ['Description', 'Qté', 'PU', 'Total'],
        rows
    )

__all__ = ['build_quotation_pdf']
