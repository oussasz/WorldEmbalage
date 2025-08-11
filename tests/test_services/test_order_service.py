from decimal import Decimal
from services.order_service import OrderService
from services.material_service import MaterialService
from models.clients import Client
from models.suppliers import Supplier


def test_create_quotation_and_convert(db_session):
    client = Client(name='Client A')
    db_session.add(client)
    supplier = Supplier(name='Supplier A')
    db_session.add(supplier)
    db_session.commit()

    svc = OrderService(db_session)
    q = svc.create_quotation(client.id, 'Q-001', Decimal('100.00'))
    assert q.reference == 'Q-001'

    order = svc.convert_to_order(q.id, 'C-001')
    assert order.reference == 'C-001'
    assert order.quotation_id == q.id
