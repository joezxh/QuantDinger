"""LLM repository for provider, api_key, model, and call_log operations."""
from datetime import datetime, timezone

from sqlalchemy import select, desc, func

from app.database.repositories.base import BaseRepository
from app.models.llm import LLmApiKey, LLmCallLog, LLmModel, LLmProvider


class LLmRepository(BaseRepository):
    # ---- Provider ----
    def get_provider_by_id(self, provider_id: int):
        return self.session.get(LLmProvider, provider_id)

    def get_provider_by_code(self, code: str):
        stmt = select(LLmProvider).where(LLmProvider.code == code)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_providers(self):
        stmt = select(LLmProvider).order_by(LLmProvider.id.asc())
        return list(self.session.execute(stmt).scalars())

    def create_provider(self, *, name, code, api_type="openai", base_url="", status=1, **kwargs):
        provider = LLmProvider(name=name, code=code, api_type=api_type, base_url=base_url, status=status, **kwargs)
        self.add(provider)
        self.flush()
        return provider

    def update_provider(self, provider_id: int, **kwargs):
        provider = self.get_provider_by_id(provider_id)
        if provider:
            for k, v in kwargs.items():
                setattr(provider, k, v)
            provider.updated_at = datetime.now(timezone.utc)
            self.flush()
        return provider

    # ---- ApiKey ----
    def get_key_by_id(self, key_id: int):
        return self.session.get(LLmApiKey, key_id)

    def list_keys(self, admin: bool = False, user_id: int = 0):
        stmt = (
            select(LLmApiKey, LLmProvider.name.label("provider_name"))
            .join(LLmProvider, LLmApiKey.provider_id == LLmProvider.id)
            .order_by(LLmApiKey.id.desc())
        )
        if not admin:
            stmt = stmt.where(
                (LLmApiKey.owner_id == user_id) | (LLmApiKey.is_public == 1)
            )
        rows = self.session.execute(stmt).all()
        result = []
        for key, provider_name in rows:
            row_dict = {
                "id": key.id,
                "provider_id": key.provider_id,
                "name": key.name,
                "status": key.status,
                "weight": key.weight,
                "owner_id": key.owner_id,
                "is_public": key.is_public,
                "fail_count": key.fail_count,
                "last_used_at": key.last_used_at,
                "metrics": key.metrics,
                "created_at": key.created_at,
                "updated_at": key.updated_at,
                "provider_name": provider_name,
                "key_masked": "****",
            }
            result.append(row_dict)
        return result

    def create_key(self, **kwargs):
        key = LLmApiKey(**kwargs)
        self.add(key)
        self.flush()
        return key

    def update_key(self, key_id: int, **kwargs):
        key = self.get_key_by_id(key_id)
        if key:
            for k, v in kwargs.items():
                setattr(key, k, v)
            key.updated_at = datetime.now(timezone.utc)
            self.flush()
        return key

    # ---- Model ----
    def get_model_by_id(self, model_id: int):
        return self.session.get(LLmModel, model_id)

    def list_models(self):
        stmt = (
            select(LLmModel, LLmProvider.name.label("provider_name"))
            .join(LLmProvider, LLmModel.provider_id == LLmProvider.id)
            .order_by(LLmModel.id.desc())
        )
        rows = self.session.execute(stmt).all()
        result = []
        for model, provider_name in rows:
            row_dict = {
                "id": model.id,
                "provider_id": model.provider_id,
                "model_name": model.model_name,
                "display_name": model.display_name,
                "lb_strategy": model.lb_strategy,
                "retries": model.retries,
                "timeout": model.timeout,
                "status": model.status,
                "created_at": model.created_at,
                "updated_at": model.updated_at,
                "provider_name": provider_name,
            }
            result.append(row_dict)
        return result

    def get_model_by_name(self, model_name: str):
        stmt = (
            select(LLmModel, LLmProvider.code.label("provider_code"))
            .join(LLmProvider, LLmModel.provider_id == LLmProvider.id)
            .where(LLmModel.model_name == model_name, LLmModel.status == 1, LLmProvider.status == 1)
        )
        row = self.session.execute(stmt).first()
        if row:
            model, provider_code = row
            return {
                "id": model.id,
                "lb_strategy": model.lb_strategy,
                "retries": model.retries,
                "timeout": model.timeout,
                "provider_code": provider_code,
            }
        return None

    def get_model_config(self, model_name: str):
        stmt = select(LLmModel).where(
            LLmModel.model_name == model_name,
            LLmModel.status == 1,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            return {
                "id": model.id,
                "provider_id": model.provider_id,
                "model_name": model.model_name,
                "lb_strategy": model.lb_strategy,
                "retries": model.retries,
                "timeout": model.timeout,
                "status": model.status,
            }
        return {}

    def list_keys_for_model(self, model_name: str, user_id: int = 0):
        """Get all valid API keys for a specific model, considering permissions."""
        subq = select(LLmModel.provider_id).where(LLmModel.model_name == model_name).limit(1).scalar_subquery()
        stmt = select(LLmApiKey).where(
            LLmApiKey.provider_id == subq,
            LLmApiKey.status != 0,
            (LLmApiKey.is_public == 1) | (LLmApiKey.owner_id == user_id),
        )
        return list(self.session.execute(stmt).scalars())

    def get_key_details(self, key_id: int):
        stmt = (
            select(LLmApiKey, LLmProvider.base_url, LLmProvider.api_type, LLmProvider.code.label("provider_code"))
            .join(LLmProvider, LLmApiKey.provider_id == LLmProvider.id)
            .where(LLmApiKey.id == key_id)
        )
        row = self.session.execute(stmt).first()
        if row:
            key, base_url, api_type, provider_code = row
            return {
                "id": key.id,
                "provider_id": key.provider_id,
                "api_key_enc": key.api_key_enc,
                "status": key.status,
                "weight": key.weight,
                "owner_id": key.owner_id,
                "is_public": key.is_public,
                "fail_count": key.fail_count,
                "last_used_at": key.last_used_at,
                "metrics": key.metrics,
                "base_url": base_url,
                "api_type": api_type,
                "provider_code": provider_code,
            }
        return {}

    def create_model(self, **kwargs):
        model = LLmModel(**kwargs)
        self.add(model)
        self.flush()
        return model

    def update_model(self, model_id: int, **kwargs):
        model = self.get_model_by_id(model_id)
        if model:
            for k, v in kwargs.items():
                setattr(model, k, v)
            model.updated_at = datetime.now(timezone.utc)
            self.flush()
        return model

    # ---- CallLog + Key Stats Update ----
    def record_call_result(
        self, key_id: int, model_id: int, user_id: int,
        latency_ms: int, status_code: int, error_msg: str = None,
        prompt_tokens: int = 0, completion_tokens: int = 0,
    ):
        log = LLmCallLog(
            api_key_id=key_id,
            model_id=model_id,
            user_id=user_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            status_code=status_code,
            error_msg=error_msg,
        )
        self.add(log)

        key = self.get_key_by_id(key_id)
        if key:
            is_success = 200 <= status_code < 300
            if is_success:
                key.fail_count = 0
                key.status = 1
                key.last_used_at = datetime.now(timezone.utc)
                key.updated_at = datetime.now(timezone.utc)
            else:
                key.fail_count = (key.fail_count or 0) + 1
                key.last_used_at = datetime.now(timezone.utc)
                key.updated_at = datetime.now(timezone.utc)
                if key.fail_count >= 5:
                    key.status = 2

        self.flush()
        return log

    def get_monitor_stats(self):
        """Get last 24h call stats grouped by model/provider."""
        cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(
                LLmModel.model_name,
                LLmProvider.name.label("provider_name"),
                func.count().label("total_calls"),
                func.avg(LLmCallLog.latency_ms).label("avg_latency"),
                (
                    func.sum(func.case((LLmCallLog.status_code == 200, 1), else_=0)) * 100.0
                    / func.count()
                ).label("success_rate"),
            )
            .select_from(LLmCallLog)
            .join(LLmModel, LLmCallLog.model_id == LLmModel.id)
            .join(LLmProvider, LLmModel.provider_id == LLmProvider.id)
            .where(LLmCallLog.created_at > cutoff)
            .group_by(LLmModel.model_name, LLmProvider.name)
        )
        rows = self.session.execute(stmt).all()
        return [
            {
                "model_name": r.model_name,
                "provider_name": r.provider_name,
                "total_calls": r.total_calls,
                "avg_latency": float(r.avg_latency) if r.avg_latency else 0,
                "success_rate": float(r.success_rate) if r.success_rate else 0,
            }
            for r in rows
        ]
