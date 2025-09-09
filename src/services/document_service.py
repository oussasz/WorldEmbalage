from __future__ import annotations
from datetime import date
from decimal import Decimal
from reports.templates.purchase_order import build_purchase_order_pdf
from reports.templates.quotation import build_quotation_pdf
from reports.templates.delivery_note import build_delivery_note_pdf
from reports.templates.invoice import build_invoice_pdf
from reports.templates.labels import build_labels_pdf
from pathlib import Path


class DocumentService:
    def build_purchase_order(self, reference: str, supplier_name: str, order_date: date, lines: list[dict]) -> Path:
        return build_purchase_order_pdf(reference, supplier_name, order_date, lines)

    def build_quotation(self, reference: str, client_name: str, issue_date: date, valid_until: date | None, items: list[dict], currency: str = 'EUR') -> Path:
        return build_quotation_pdf(reference, client_name, issue_date, valid_until, items, currency)

    def build_delivery_note(self, reference: str, client_name: str, delivery_date: date, lines: list[dict], client_details: str = "") -> Path:
        return build_delivery_note_pdf(reference, client_name, delivery_date, lines, client_details)

    def build_invoice(self, invoice_number: str, client_name: str, issue_date: date, items: list[dict], currency: str = 'EUR', tva_rate: Decimal = Decimal('0.20')) -> Path:
        return build_invoice_pdf(invoice_number, client_name, issue_date, items, currency, tva_rate)

    def build_labels(self, title: str, labels: list[str]) -> Path:
        return build_labels_pdf(title, labels)

__all__ = ['DocumentService']
