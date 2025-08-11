from __future__ import annotations
from typing import Generic, TypeVar, Type, Iterable
from sqlalchemy.orm import Session

T = TypeVar('T')


class Repository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id_: int) -> T | None:
        return self.db.get(self.model, id_)

    def add(self, instance: T) -> T:
        self.db.add(instance)
        return instance

    def list(self) -> Iterable[T]:
        return self.db.query(self.model).all()

    def delete(self, instance: T):
        self.db.delete(instance)

    def commit(self):
        self.db.commit()

    def flush(self):
        self.db.flush()

__all__ = ['Repository']
