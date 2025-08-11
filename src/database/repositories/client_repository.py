from __future__ import annotations
from database.repositories.base import Repository
from models.clients import Client


class ClientRepository(Repository[Client]):
    def __init__(self, db):
        super().__init__(db, Client)

__all__ = ['ClientRepository']
