"""Initial schema migration — all tables consolidated into one version.

This migration replaces the legacy init.sql auto-execution mechanism.
All tables (002-007) have been merged into this single version.

Revision ID: 001_initial_schema
Create Date: 2026-04-25
"""
import os
import sys

# Ensure the project root is importable
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from alembic import op
import sqlalchemy as sa

# Import all models to register them with Base.metadata
from app.models.base import Base
from app.models import (  # noqa: F401
    AiCalibration,
    AnalysisMemory,
    AnalysisResult,
    AnalysisTask,
    ApiKey,
    BacktestEquityPoint,
    BacktestResult,
    BacktestTrade,
    BillingRecord,
    CollectionRecord,
    CommunityIndicator,
    CompanyNarrativeFeature,
    CreditsLog,
    CryptoNarrativeFeature,
    DataSourceConfig,
    DataSourceDataset,
    DifyWorkflow,
    DifyWorkflowLog,
    ExchangeCredential,
    GraphEntityRef,
    GraphEpisode,
    GraphFeatureDaily,
    GraphJob,
    GraphRelationSnapshot,
    IndicatorCode,
    IndicatorComment,
    IndicatorPurchase,
    LLmApiKey,
    LLmCallLog,
    LLmModel,
    LLmProvider,
    LoginAttempt,
    ManualPosition,
    MarketKline,
    MarketPrice,
    MarketSymbol,
    MembershipOrder,
    OAuthLink,
    OAuthState,
    PendingOrder,
    PolymarketAnalysis,
    PolymarketMarket,
    PolymarketMarketFeature,
    PolymarketOpportunity,
    PolymarketUser,
    PositionAlert,
    PositionMonitor,
    QueryCache,
    QuickTrade,
    SecurityLog,
    Strategy,
    StrategyLog,
    StrategyNotification,
    StrategyPosition,
    StrategyTrade,
    StrategyTrading,
    TradeOrder,
    UsdtOrder,
    User,
    VerificationCode,
    Watchlist,
)

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    existing = set(sa.inspect(conn).get_table_names())

    for table in Base.metadata.sorted_tables:
        if table.name in existing:
            continue
        table.create(conn)


def downgrade():
    conn = op.get_bind()
    for table in reversed(Base.metadata.sorted_tables):
        table.drop(conn, checkfirst=True)
