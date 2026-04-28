"""API Routes Module"""
from flask import Flask


def register_routes(app: Flask):
    """Register all API route blueprints"""
    from app.routes.kline import kline_bp
    from app.routes.backtest import backtest_bp
    from app.routes.health import health_bp
    from app.routes.market import market_bp
    from app.routes.strategy import strategy_bp
    from app.routes.credentials import credentials_bp
    from app.routes.auth import auth_bp
    from app.routes.ai.ai_chat import ai_chat_bp
    from app.routes.indicator import indicator_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.settings import settings_bp
    from app.routes.portfolio import portfolio_bp
    from app.routes.ibkr import ibkr_bp
    from app.routes.mt5 import mt5_bp
    from app.routes.user import user_bp
    from app.routes.global_market import global_market_bp
    from app.routes.community import community_bp
    from app.routes.fast_analysis import fast_analysis_bp
    from app.routes.billing import billing_bp
    from app.routes.quick_trade import quick_trade_bp
    from app.routes.polymarket import polymarket_bp
    from app.routes.experiment import experiment_bp
    from app.routes.llm import llm_bp
    from app.routes.graph_analysis import graph_analysis_bp
    from app.routes.stock_news_graph_poc import stock_news_graph_poc_bp
    from app.routes.domain_graph import stock_graph_bp, crypto_graph_bp, polymarket_graph_bp
    from app.routes.dify_workflow import dify_bp
    from app.routes.data_source import data_source_bp
    from app.routes.permission import permission_bp
    from app.routes.sync import sync_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(kline_bp, url_prefix='/api/indicator')
    app.register_blueprint(backtest_bp, url_prefix='/api/indicator')
    app.register_blueprint(market_bp, url_prefix='/api/market')
    app.register_blueprint(ai_chat_bp, url_prefix='/api/ai')
    app.register_blueprint(indicator_bp, url_prefix='/api/indicator')
    app.register_blueprint(strategy_bp, url_prefix='/api')
    app.register_blueprint(credentials_bp, url_prefix='/api/credentials')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(ibkr_bp, url_prefix='/api/ibkr')
    app.register_blueprint(mt5_bp, url_prefix='/api/mt5')
    app.register_blueprint(global_market_bp, url_prefix='/api/global-market')
    app.register_blueprint(community_bp, url_prefix='/api/community')
    app.register_blueprint(fast_analysis_bp, url_prefix='/api/fast-analysis')
    app.register_blueprint(billing_bp, url_prefix='/api/billing')
    app.register_blueprint(quick_trade_bp, url_prefix='/api/quick-trade')
    app.register_blueprint(polymarket_bp, url_prefix='/api/polymarket')
    app.register_blueprint(experiment_bp, url_prefix='/api/experiment')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')
    app.register_blueprint(graph_analysis_bp, url_prefix='/api/graph-analysis')
    app.register_blueprint(stock_news_graph_poc_bp, url_prefix='/api/graph-poc/stock-news')
    app.register_blueprint(stock_graph_bp, url_prefix='/api/graph/stock')
    app.register_blueprint(crypto_graph_bp, url_prefix='/api/graph/crypto')
    app.register_blueprint(polymarket_graph_bp, url_prefix='/api/graph/polymarket')
    app.register_blueprint(dify_bp)
    app.register_blueprint(data_source_bp, url_prefix='/api/data-source')
    app.register_blueprint(permission_bp, url_prefix='/api/permission')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
