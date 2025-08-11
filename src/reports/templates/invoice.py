from __future__ import annotations
from reports.pdf_generator import PDFGenerator
from pathlib import Path
from datetime import date
from decimal import Decimal


def build_invoice_pdf(invoice_number: str, client_name: str, issue_date: date, items: list[dict], currency: str = 'EUR', tva_rate: Decimal = Decimal('0.20')) -> Path:
    gen = PDFGenerator()
    total_ht = Decimal('0')
    rows: list[list[str]] = []
    for it in items:
        line_total = Decimal(str(it['unit_price'])) * it['quantity']
        total_ht += line_total
        rows.append([
            it['description'],
            str(it['quantity']),
            f"{it['unit_price']}",
            f"{line_total}"
        ])
    tva = (total_ht * tva_rate).quantize(Decimal('0.01'))
    total_ttc = total_ht + tva
    rows.append(['', '', 'TOTAL HT', f"{total_ht} {currency}"])
    rows.append(['', '', f"TVA {tva_rate * 100}%", f"{tva} {currency}"])
    rows.append(['', '', 'TOTAL TTC', f"{total_ttc} {currency}"])
    return gen.build_table_doc(
        f"Facture {invoice_number}",
        ['Description', 'Qté', 'PU', 'Total'],
        rows
    )

__all__ = ['build_invoice_pdf']
