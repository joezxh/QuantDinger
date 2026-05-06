"""
实体去重与关系识别模型
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, DECIMAL, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base


class EntityFinancialInstitution(Base):
    """全局金融机构实体表（去重核心）"""
    __tablename__ = 'entity_financial_institutions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 标准名称
    standard_name = Column(String(500), nullable=False, unique=True, comment='标准化名称')
    short_name = Column(String(200), comment='简称')
    
    # 机构类型
    institution_type = Column(String(50), nullable=False, comment='fund/insurance/bank/government/corporate')
    
    # 识别信息
    cik = Column(String(20), comment='SEC CIK编号')
    lei = Column(String(20), comment='法律实体标识符')
    bloomberg_id = Column(String(50), comment='Bloomberg ID')
    reuters_id = Column(String(50), comment='Reuters ID')
    
    # 关联信息
    parent_institution_id = Column(BigInteger, ForeignKey('entity_financial_institutions.id'), comment='母公司')
    country = Column(String(50), comment='注册国家')
    headquarters = Column(String(200), comment='总部')
    website = Column(String(500), comment='官网')
    
    # 统计信息
    total_companies_held = Column(Integer, default=0, comment='持股公司数')
    total_market_value = Column(DECIMAL(24, 8), comment='总持仓市值')
    
    # 元数据
    description = Column(Text, comment='机构描述')
    payload_json = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class EntityInstitutionAlias(Base):
    """机构名称别名表（用于去重映射）"""
    __tablename__ = 'entity_institution_aliases'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    institution_id = Column(BigInteger, ForeignKey('entity_financial_institutions.id'), nullable=False)
    
    # 别名信息
    alias_name = Column(String(500), nullable=False, comment='别名/变体名称')
    alias_source = Column(String(100), comment='来源 (13F/SEC/manual)')
    confidence = Column(DECIMAL(5, 4), default=1.0, comment='匹配置信度')
    is_verified = Column(Boolean, default=False, comment='是否已验证')
    
    # 匹配规则
    match_type = Column(String(30), comment='exact/fuzzy/abbreviation')
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class EntityIndividualShareholder(Base):
    """全局个人股东实体表"""
    __tablename__ = 'entity_individual_shareholders'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    standard_name = Column(String(500), nullable=False, unique=True)
    
    # 识别信息（隐私保护 - 哈希存储）
    national_id_hash = Column(String(64), comment='身份证号哈希')
    passport_hash = Column(String(64), comment='护照号哈希')
    
    # 关联信息
    related_companies = Column(Integer, default=0, comment='关联公司数')
    is_insider = Column(Boolean, default=False, comment='是否内部人')
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class EntityPolymarketUser(Base):
    """Polymarket 全局账号实体表（去重核心）"""
    __tablename__ = 'entity_polymarket_users'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 主钱包
    primary_wallet = Column(String(255), unique=True, nullable=False, comment='主钱包地址')
    
    # 用户信息
    display_name = Column(String(255), comment='显示名称')
    profile_image_url = Column(String(1000), comment='头像')
    
    # 关联钱包
    linked_wallets = Column(ARRAY(String), comment='关联钱包地址数组')
    
    # 交易统计
    total_volume = Column(DECIMAL(24, 8), default=0)
    total_trades = Column(Integer, default=0)
    win_rate = Column(DECIMAL(10, 4))
    profit_loss = Column(DECIMAL(24, 8))
    
    # 关系网络
    connected_users = Column(Integer, default=0, comment='关联用户数')
    network_centrality = Column(DECIMAL(10, 6), comment='网络中心度')
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class EntityPolymarketWalletLink(Base):
    """Polymarket 钱包关联表"""
    __tablename__ = 'entity_polymarket_wallet_links'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('entity_polymarket_users.id'), nullable=False)
    
    wallet_address = Column(String(255), nullable=False, comment='钱包地址')
    is_primary = Column(Boolean, default=False, comment='是否主钱包')
    
    # 关联依据
    link_reason = Column(String(100), comment='关联原因')
    confidence = Column(DECIMAL(5, 4), comment='匹配置信度')
    
    # 时间
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class EntityRelationship(Base):
    """实体关系图（通用关系表）"""
    __tablename__ = 'entity_relationships'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 关系两端
    source_entity_type = Column(String(50), nullable=False, comment='institution/individual/polymarket_user')
    source_entity_id = Column(BigInteger, nullable=False)
    target_entity_type = Column(String(50), nullable=False)
    target_entity_id = Column(BigInteger, nullable=False)
    
    # 关系类型
    relationship_type = Column(String(100), nullable=False, comment='same_entity/subsidiary/competitor/frequent_counterparty')
    
    # 关系强度
    strength = Column(DECIMAL(10, 6), comment='关系强度 0-1')
    evidence_count = Column(Integer, default=0, comment='证据数量')
    
    # 关系描述
    description = Column(Text)
    payload_json = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class PolymarketTradingNetwork(Base):
    """Polymarket 交易关系网络表"""
    __tablename__ = 'polymarket_trading_network'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 交易双方
    user_a_id = Column(BigInteger, ForeignKey('entity_polymarket_users.id'))
    user_b_id = Column(BigInteger, ForeignKey('entity_polymarket_users.id'))
    
    # 关系统计
    trade_count = Column(Integer, default=0, comment='交易次数')
    total_volume = Column(DECIMAL(24, 8), comment='总交易量')
    first_trade_at = Column(DateTime(timezone=True), comment='首次交易')
    last_trade_at = Column(DateTime(timezone=True), comment='最后交易')
    
    # 关系类型
    relationship_type = Column(String(50), comment='frequent_counterparty/occasional/rare')
    
    # 共同市场
    common_markets = Column(ARRAY(String), comment='共同参与的市场列表')
    common_categories = Column(ARRAY(String), comment='共同参与的类别')
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
