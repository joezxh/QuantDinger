"""Model imports for SQLAlchemy metadata registration."""
from app.models.analysis import AiCalibration, AnalysisResult
from app.models.analysis_task import AnalysisMemory, AnalysisTask
from app.models.auth_security import LoginAttempt, OAuthState, SecurityLog
from app.models.backtest import BacktestEquityPoint, BacktestResult, BacktestTrade
from app.models.billing import BillingRecord
from app.models.collection import CollectionRecord
from app.models.community import CommunityIndicator
from app.models.credits import CreditsLog
from app.models.data_source_meta import ApiKey, DataSourceConfig, DataSourceDataset, QueryCache
from app.models.dify import DifyWorkflow, DifyWorkflowLog
from app.models.exchange import ExchangeCredential
from app.models.graph_domain import (
    CompanyNarrativeFeature,
    CryptoNarrativeFeature,
    PolymarketMarketFeature,
)
from app.models.graph_meta import (
    GraphEntityRef,
    GraphEpisode,
    GraphFeatureDaily,
    GraphJob,
    GraphRelationSnapshot,
)
from app.models.indicator_full import IndicatorCode, IndicatorComment, IndicatorPurchase
from app.models.llm import LLmApiKey, LLmCallLog, LLmModel, LLmProvider
from app.models.market import MarketKline, MarketPrice
from app.models.market_symbol import MarketSymbol
from app.models.membership import MembershipOrder, UsdtOrder
from app.models.notification import StrategyLog, StrategyNotification
from app.models.order import PendingOrder, QuickTrade
from app.models.permission import Permission, Role, RolePermission, UserRole
from app.models.polymarket import (
    PolymarketAnalysis,
    PolymarketMarket,
    PolymarketOpportunity,
    PolymarketUser,
)
from app.models.position import ManualPosition, PositionAlert, PositionMonitor, StrategyPosition
from app.models.strategy import Strategy, StrategyTrading
from app.models.trading import StrategyTrade, TradeOrder
from app.models.user import User
from app.models.verification import OAuthLink, VerificationCode
from app.models.watchlist import Watchlist

__all__ = [
    "AnalysisMemory",
    "AiCalibration",
    "AnalysisResult",
    "AnalysisTask",
    "BacktestEquityPoint",
    "BacktestResult",
    "BacktestTrade",
    "BillingRecord",
    "CollectionRecord",
    "CommunityIndicator",
    "CompanyNarrativeFeature",
    "CreditsLog",
    "CryptoNarrativeFeature",
    "DataSourceDataset",
    "DataSourceConfig",
    "ApiKey",
    "QueryCache",
    "DifyWorkflow",
    "DifyWorkflowLog",
    "ExchangeCredential",
    "GraphEntityRef",
    "GraphEpisode",
    "GraphFeatureDaily",
    "GraphJob",
    "GraphRelationSnapshot",
    "IndicatorCode",
    "IndicatorComment",
    "IndicatorPurchase",
    "LLmApiKey",
    "LLmCallLog",
    "LLmModel",
    "LLmProvider",
    "LoginAttempt",
    "ManualPosition",
    "MarketKline",
    "MarketPrice",
    "MarketSymbol",
    "MembershipOrder",
    "OAuthLink",
    "OAuthState",
    "PendingOrder",
    "Permission",
    "PolymarketAnalysis",
    "PolymarketMarket",
    "PolymarketMarketFeature",
    "PolymarketOpportunity",
    "PolymarketUser",
    "PositionAlert",
    "PositionMonitor",
    "QuickTrade",
    "Role",
    "RolePermission",
    "SecurityLog",
    "Strategy",
    "StrategyLog",
    "StrategyNotification",
    "StrategyPosition",
    "StrategyTrading",
    "StrategyTrade",
    "TradeOrder",
    "UsdtOrder",
    "User",
    "UserRole",
    "VerificationCode",
    "Watchlist",
]
