"""Exchange credential repository."""
from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.exchange import ExchangeCredential


class ExchangeRepository(BaseRepository):
    def get_by_id(self, credential_id: int):
        return self.session.get(ExchangeCredential, credential_id)

    def list_by_user(self, user_id: int):
        stmt = (
            select(ExchangeCredential)
            .where(ExchangeCredential.user_id == user_id)
            .order_by(desc(ExchangeCredential.created_at))
        )
        return list(self.session.execute(stmt).scalars())

    def get_by_exchange(self, user_id: int, exchange_id: str):
        stmt = (
            select(ExchangeCredential)
            .where(
                ExchangeCredential.user_id == user_id,
                ExchangeCredential.exchange_id == exchange_id,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_credential(self, **kwargs):
        credential = ExchangeCredential(**kwargs)
        self.add(credential)
        self.flush()
        return credential

    def update_credential(self, credential_id: int, **kwargs):
        credential = self.get_by_id(credential_id)
        if credential:
            for k, v in kwargs.items():
                setattr(credential, k, v)
            self.flush()
        return credential

    def delete_credential(self, credential_id: int):
        credential = self.get_by_id(credential_id)
        if credential:
            self.session.delete(credential)
            self.flush()
            return True
        return False
