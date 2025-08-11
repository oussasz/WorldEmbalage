from datetime import date
from services.document_service import DocumentService
from decimal import Decimal


def test_generate_quotation_pdf(tmp_path):
    svc = DocumentService()
    path = svc.build_quotation(
        'Q-TEST', 'Client Test', date.today(), None,
        items=[{'description': 'Produit A', 'quantity': 10, 'unit_price': '5.50'}]
    )
    assert path.exists()
    assert path.stat().st_size > 0


def test_generate_invoice_pdf(tmp_path):
    svc = DocumentService()
    path = svc.build_invoice(
        'INV-TEST', 'Client Test', date.today(),
        items=[{'description': 'Produit A', 'quantity': 2, 'unit_price': '10.00'}],
        tva_rate=Decimal('0.20')
    )
    assert path.exists()
    assert path.stat().st_size > 0
