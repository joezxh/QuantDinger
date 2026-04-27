"""Credential repository helpers."""
from sqlalchemy import delete, select

from app.database.repositories.base import BaseRepository
from app.models.exchange import ExchangeCredential


class CredentialRepository(BaseRepository):
    def list_user_credentials(self, user_id: int):
        stmt = select(ExchangeCredential).where(ExchangeCredential.user_id == user_id).order_by(ExchangeCredential.id.desc())
        return list(self.session.execute(stmt).scalars())

    def create_credential(self, **kwargs):
        row = ExchangeCredential(**kwargs)
        self.add(row)
        self.flush()
        return row

    def delete_credential(self, cred_id: int, user_id: int):
        self.session.execute(delete(ExchangeCredential).where(ExchangeCredential.id == cred_id, ExchangeCredential.user_id == user_id))

    def get_credential(self, cred_id: int, user_id: int):
        stmt = select(ExchangeCredential).where(ExchangeCredential.id == cred_id, ExchangeCredential.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()
