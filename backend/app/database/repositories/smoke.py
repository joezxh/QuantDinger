"""Smoke checks for graph ORM repositories."""
from app.database.repositories.backtest_repository import BacktestRepository
from app.database.repositories.billing_repository import BillingRepository
from app.database.repositories.community_repository import CommunityRepository
from app.database.repositories.graph_repository import GraphRepository
from app.database.repositories.market_repository import MarketRepository
from app.database.repositories.polymarket_repository import PolymarketRepository
from app.database.repositories.user_repository import UserRepository


class GraphOrmSmoke:
    def __init__(self, session):
        self.market_repo = MarketRepository(session)
        self.graph_repo = GraphRepository(session)
        self.user_repo = UserRepository(session)
        self.billing_repo = BillingRepository(session)
        self.community_repo = CommunityRepository(session)
        self.polymarket_repo = PolymarketRepository(session)
        self.backtest_repo = BacktestRepository(session)

    def check_repositories(self):
        return {
            "market_repo": isinstance(self.market_repo, MarketRepository),
            "graph_repo": isinstance(self.graph_repo, GraphRepository),
            "user_repo": isinstance(self.user_repo, UserRepository),
            "billing_repo": isinstance(self.billing_repo, BillingRepository),
            "community_repo": isinstance(self.community_repo, CommunityRepository),
            "polymarket_repo": isinstance(self.polymarket_repo, PolymarketRepository),
            "backtest_repo": isinstance(self.backtest_repo, BacktestRepository),
            "market_repo_has_collection_save": hasattr(self.market_repo, "save_collection_record"),
            "graph_repo_has_save_episode": hasattr(self.graph_repo, "save_episode"),
            "graph_repo_has_mark_episode_status": hasattr(self.graph_repo, "mark_episode_status"),
            "graph_repo_has_create_graph_job": hasattr(self.graph_repo, "create_graph_job"),
            "graph_repo_has_update_graph_job": hasattr(self.graph_repo, "update_graph_job"),
            "graph_repo_has_feature_insert": hasattr(self.graph_repo, "insert_feature_batch"),
            "graph_repo_has_domain_feature_insert": hasattr(self.graph_repo, "insert_company_narrative_features"),
            "user_repo_has_lookup": hasattr(self.user_repo, "get_by_username"),
            "billing_repo_has_credit_lookup": hasattr(self.billing_repo, "get_user_credits"),
            "community_repo_has_market_list": hasattr(self.community_repo, "list_published_indicators"),
            "polymarket_repo_has_market_lookup": hasattr(self.polymarket_repo, "get_market_by_market_id"),
            "backtest_repo_has_user_runs": hasattr(self.backtest_repo, "list_user_runs"),
        }
