from __future__ import annotations
from database.repositories.base import Repository
from models.orders import ClientOrder, Quotation, SupplierOrder


class ClientOrderRepository(Repository[ClientOrder]):
    def __init__(self, db):
        super().__init__(db, ClientOrder)


class QuotationRepository(Repository[Quotation]):
    def __init__(self, db):
        super().__init__(db, Quotation)


class SupplierOrderRepository(Repository[SupplierOrder]):
    def __init__(self, db):
        super().__init__(db, SupplierOrder)

__all__ = ['ClientOrderRepository', 'QuotationRepository', 'SupplierOrderRepository']
