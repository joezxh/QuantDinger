"""SQLAlchemy models for data source configuration and return structure metadata."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DataSourceConfig(Base):
    """
    Data source access configuration.

    One row per logical data source / provider, storing its access parameters
    (base URLs, timeout, retry, default exchange, etc.) and load balancing
    strategy.

    Actual API key values are stored encrypted in the llm_api_keys table,
    associated via source_config_id → api_keys relationship.
    """

    __tablename__ = "data_data_source_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_code: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(150), nullable=False)
    layer: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="data_source"
    )
    # ^ data_source / data_provider / fundamental / sentiment / collector
    market_categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )
    # ^ e.g. {"Crypto", "USStock", "Forex"}
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # Load balancing strategy for multi-key scheduling
    # round_robin / weighted / health_first / random
    load_balance_strategy: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="round_robin"
    )

    # Access parameters stored as flexible JSONB:
    # {
    #   "api_key_env": "TWELVE_DATA_API_KEY",       # reference env var name
    #   "api_key_required": false,                    # whether API key is mandatory
    #   "base_url": "https://api.twelvedata.com/time_series",
    #   "fallback_base_url": "https://...",
    #   "timeout_sec": 20,
    #   "retry_count": 3,
    #   "default_exchange": "coinbase",
    #   "rate_limit_per_min": 8,
    #   "proxy_supported": true,
    #   "notes": "..."
    # }
    config_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # List of source_code values this data source depends on
    dependencies: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(80)), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    datasets: Mapped[list["DataSourceDataset"]] = relationship(
        "DataSourceDataset",
        back_populates="source",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey",
        back_populates="source_config",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<DataSourceConfig(code={self.source_code}, "
            f"layer={self.layer}, balance={self.load_balance_strategy})>"
        )


class ApiKey(Base):
    """
    Independent API key management table.

    Stores encrypted API key values, supports public (shared) and private
    (per-user) keys, tracks health and usage for load balancing.

    Encryption: AES-256-GCM via CryptoUtils (crypto.py), using LLM_KEY_SECRET
    """

    __tablename__ = "data_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_config_id: Mapped[int] = mapped_column(
        ForeignKey("data_data_source_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    key_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="public"
    )
    # ^ public  = 系统预设共享密钥，所有用户可使用
    #   private = 用户个人配置的专属密钥，仅该用户可使用

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Owner user for private keys; NULL for public keys",
    )

    # Human-readable label, e.g. "TwelveData Key #1"
    key_alias: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # AES-256-GCM encrypted API key value
    encrypted_key_value: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    # Truncated hint for display, e.g. "****a1b2"
    key_hint: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="active"
    )
    # ^ active / disabled / rate_limited / expired / error

    # Weight for weighted load balancing
    weight: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )

    # Health tracking
    consecutive_errors: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Automatically disable after N consecutive errors
    max_consecutive_errors: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="5"
    )

    # Rate limit tracking
    daily_call_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    current_daily_calls: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    last_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Total call counter (lifetime)
    total_calls: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    created_by: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Admin user ID who added this key",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    source_config: Mapped["DataSourceConfig"] = relationship(
        "DataSourceConfig", back_populates="api_keys"
    )

    def __repr__(self) -> str:
        return (
            f"<ApiKey(id={self.id}, source={self.source_config_id}, "
            f"type={self.key_type}, status={self.status})>"
        )


class DataSourceDataset(Base):
    """
    Return structure metadata for a dataset produced by a data source/provider.

    Each row describes one dataset (e.g. "crypto_prices", "stock_indices", "heatmap"),
    including its fields schema, sample output, and coverage info.
    """

    __tablename__ = "data_data_source_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_data_source_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_code: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False
    )
    # ^ e.g. "crypto_prices", "forex_pairs", "fear_greed"
    dataset_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    function_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    # ^ e.g. "fetch_crypto_prices()"
    return_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="list[dict]"
    )
    # ^ list[dict] / dict / list / str / scalar

    # Detailed field schema — array of field descriptors:
    # [
    #   {"name": "symbol",     "type": "str",   "description": "币种符号",
    #    "nullable": false,    "example": "BTC"},
    #   {"name": "price",      "type": "float", "description": "当前价格 (USD)",
    #    "nullable": false,    "example": 65000.0},
    #   ...
    # ]
    fields_schema: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Sample output (1~2 records for illustration)
    sample_output: Mapped[dict | list | None] = mapped_column(
        JSONB, nullable=True
    )

    # Coverage / scope description
    coverage_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ^ e.g. "覆盖15个主流币：BTC, ETH, SOL, XRP, ADA..."

    # Source file reference
    source_file_ref: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # ^ e.g. "app/data_providers/crypto.py"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    source: Mapped["DataSourceConfig"] = relationship(
        "DataSourceConfig", back_populates="datasets"
    )

    # Cache entries for this dataset
    cache_entries: Mapped[list["QueryCache"]] = relationship(
        "QueryCache", back_populates="dataset_ref",
        lazy="dynamic", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<DataSourceDataset(code={self.dataset_code}, "
            f"return_type={self.return_type})>"
        )


class QueryCache(Base):
    """
    Query result cache with deduplication support.

    Each unique query (normalised) gets a deterministic cache_key.
    When multiple users / requests hit the same query, the system
    reuses the cached result instead of re-fetching from upstream.

    Status tracking (pending → running → completed / failed) prevents
    duplicate requests from submitting identical fetch jobs concurrently.
    """

    __tablename__ = "data_query_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Deterministic SHA-256 hash of NORMALIZED query parameters
    cache_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )

    # Link back to the dataset definition
    dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("data_data_source_datasets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Denormalised source identifier for quick lookup
    source_code: Mapped[str] = mapped_column(
        String(80), nullable=False
    )

    # Full query parameters used to generate this cache entry
    query_params: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Cached result payload
    result_data: Mapped[dict | list | None] = mapped_column(
        JSONB, nullable=True
    )
    result_size_bytes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # Status for dedup control
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    # ^ pending / running / completed / failed / expired

    # Error info
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Usage tracking
    request_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )
    # How many distinct user/request contexts asked for this query

    # TTL
    ttl_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="300"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    first_requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    dataset_ref: Mapped["DataSourceDataset | None"] = relationship(
        "DataSourceDataset", back_populates="cache_entries"
    )

    def __repr__(self) -> str:
        return (
            f"<QueryCache(key={self.cache_key[:12]}..., "
            f"source={self.source_code}, status={self.status})>"
        )
