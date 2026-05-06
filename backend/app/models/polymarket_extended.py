"""
Polymarket 扩展数据模型（账号/订单/持仓/交易历史）
"""
from sqlalchemy import Column, BigInteger, String, DateTime, DECIMAL, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base


class PolymarketAccount(Base):
    """Polymarket 用户账号表"""
    __tablename__ = 'polymarket_accounts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 关联系统用户
    user_id = Column(Integer, comment='关联 sys_users.id')
    
    # 链上信息
    wallet_address = Column(String(255), unique=True, nullable=False, comment='钱包地址')
    network = Column(String(50), default='polygon', comment='区块链网络')
    
    # 账户信息
    display_name = Column(String(255), comment='显示名称')
    profile_image_url = Column(String(1000), comment='头像URL')
    
    # 交易统计
    total_volume = Column(DECIMAL(24, 8), default=0, comment='总交易量')
    total_trades = Column(Integer, default=0, comment='总交易次数')
    win_rate = Column(DECIMAL(10, 4), comment='胜率')
    profit_loss = Column(DECIMAL(24, 8), comment='盈亏')
    
    # 持仓信息
    portfolio_value = Column(DECIMAL(24, 8), comment='当前持仓价值')
    cash_balance = Column(DECIMAL(24, 8), comment='现金余额')
    
    # 实体关联
    entity_user_id = Column(BigInteger, comment='关联 entity_polymarket_users.id')
    
    # 元数据
    payload_json = Column(JSONB, comment='原始完整数据')
    last_synced_at = Column(DateTime(timezone=True), comment='最后同步时间')
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class PolymarketOrder(Base):
    """Polymarket 市场订单表"""
    __tablename__ = 'polymarket_orders'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 关联信息
    account_id = Column(BigInteger, ForeignKey('polymarket_accounts.id'), comment='关联账号')
    market_id = Column(String(255), nullable=False, comment='市场ID')
    user_id = Column(Integer, comment='系统用户ID')
    
    # 订单信息
    order_id = Column(String(255), unique=True, nullable=False, comment='Polymarket订单ID')
    side = Column(String(10), nullable=False, comment='buy/sell')
    asset = Column(String(100), nullable=False, comment='资产名称 (YES/NO)')
    
    # 价格信息
    price = Column(DECIMAL(10, 4), nullable=False, comment='成交价格')
    size = Column(DECIMAL(24, 8), nullable=False, comment='数量')
    filled_size = Column(DECIMAL(24, 8), default=0, comment='已成交数量')
    
    # 状态信息
    status = Column(String(30), default='open', comment='open/filled/cancelled/expired')
    order_type = Column(String(30), comment='market/limit')
    
    # 时间信息
    created_at_iso = Column(String(64), comment='Polymarket创建时间')
    last_updated_iso = Column(String(64), comment='Polymarket更新时间')
    
    # 交易费用
    fees = Column(DECIMAL(24, 8), comment='手续费')
    
    # 元数据
    transaction_hash = Column(String(255), comment='链上交易哈希')
    payload_json = Column(JSONB, comment='原始完整数据')
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class PolymarketPosition(Base):
    """Polymarket 持仓表"""
    __tablename__ = 'polymarket_positions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    account_id = Column(BigInteger, ForeignKey('polymarket_accounts.id'))
    market_id = Column(String(255), nullable=False)
    user_id = Column(Integer)
    
    # 持仓信息
    asset = Column(String(100), nullable=False, comment='YES/NO')
    quantity = Column(DECIMAL(24, 8), nullable=False, comment='持仓数量')
    average_price = Column(DECIMAL(10, 4), comment='平均成本')
    current_price = Column(DECIMAL(10, 4), comment='当前价格')
    
    # 盈亏信息
    unrealized_pnl = Column(DECIMAL(24, 8), comment='未实现盈亏')
    realized_pnl = Column(DECIMAL(24, 8), comment='已实现盈亏')
    
    # 状态
    status = Column(String(30), default='open', comment='open/closed')
    
    payload_json = Column(JSONB)
    last_synced_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class PolymarketTradeHistory(Base):
    """Polymarket 交易历史表"""
    __tablename__ = 'polymarket_trade_history'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    account_id = Column(BigInteger, ForeignKey('polymarket_accounts.id'))
    market_id = Column(String(255), nullable=False)
    user_id = Column(Integer)
    
    # 交易信息
    trade_id = Column(String(255), unique=True, nullable=False)
    side = Column(String(10), nullable=False, comment='buy/sell')
    asset = Column(String(100), nullable=False)
    
    # 价格数量
    price = Column(DECIMAL(10, 4), nullable=False)
    quantity = Column(DECIMAL(24, 8), nullable=False)
    total_value = Column(DECIMAL(24, 8), comment='总价值')
    
    # 时间信息
    traded_at = Column(DateTime(timezone=True), nullable=False)
    
    # 关联订单
    order_id = Column(String(255))
    
    # 元数据
    counterparty = Column(String(255), comment='交易对手')
    payload_json = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
