from services.production_service import ProductionService
from services.order_service import OrderService
from services.material_service import MaterialService
from models.clients import Client
from models.suppliers import Supplier
from models.orders import Quotation
from models.production import ProductionStage
from decimal import Decimal


def test_create_batch(db_session):
    client = Client(name='Client B')
    supplier = Supplier(name='Supplier B')
    db_session.add_all([client, supplier])
    db_session.commit()

    order_svc = OrderService(db_session)
    q = order_svc.create_quotation(client.id, 'Q-002', Decimal('200.00'))
    order = order_svc.convert_to_order(q.id, 'C-002')

    prod_svc = ProductionService(db_session)
    batch = prod_svc.create_batch(order.id, 'BATCH-01')
    assert batch.batch_code == 'BATCH-01'


def test_advance_stage(db_session):
    client = Client(name='Client C')
    db_session.add(client)
    db_session.commit()
    order_svc = OrderService(db_session)
    q = order_svc.create_quotation(client.id, 'Q-003', Decimal('300.00'))
    order = order_svc.convert_to_order(q.id, 'C-003')
    prod_svc = ProductionService(db_session)
    batch = prod_svc.create_batch(order.id, 'BATCH-02')
    prod_svc.advance_stage(batch.id, ProductionStage.GLUE_ECLIPSAGE)
    refreshed = db_session.get(type(batch), batch.id)
    assert refreshed.stage == ProductionStage.GLUE_ECLIPSAGE
