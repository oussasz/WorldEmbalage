from services.material_service import MaterialService
from models.suppliers import Supplier


def test_create_supplier_order_and_reception(db_session):
    supplier = Supplier(name='Supplier X')
    db_session.add(supplier)
    db_session.commit()

    svc = MaterialService(db_session)
    order = svc.create_supplier_order(supplier.id, 'SO-001')
    assert order.reference == 'SO-001'

    reception = svc.record_reception(order.id, 50)
    assert reception.quantity == 50
