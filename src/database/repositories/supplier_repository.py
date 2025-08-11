from __future__ import annotations
from database.repositories.base import Repository
from models.suppliers import Supplier


class SupplierRepository(Repository[Supplier]):
    def __init__(self, db):
        super().__init__(db, Supplier)

__all__ = ['SupplierRepository']
