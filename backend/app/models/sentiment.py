"""
市场情绪数据模型
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, DECIMAL, Integer, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base


class SentimentMarketIndicator(Base):
    """市场情绪指标表"""
    __tablename__ = 'sentiment_market_indicators'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 指标类型
    indicator_type = Column(String(50), nullable=False, 
                           comment='指标类型 (fear_greed/vix/put_call/social_media)')
    indicator_name = Column(String(100), nullable=False, comment='指标名称')
    
    # 数值
    value = Column(DECIMAL(10, 4), comment='当前值')
    change = Column(DECIMAL(10, 4), comment='变动值')
    change_percent = Column(DECIMAL(10, 4), comment='变动百分比')
    
    # 分级
    level = Column(String(50), comment='等级 (extreme_fear/fear/neutral/greed/extreme_greed)')
    signal = Column(String(20), comment='信号 (bullish/bearish/neutral)')
    
    # 关联市场
    market = Column(String(50), comment='关联市场')
    symbol = Column(String(50), comment='关联标的')
    
    # 时间
    measured_at = Column(DateTime(timezone=True), nullable=False, comment='测量时间')
    
    # 来源
    source = Column(String(100), comment='数据来源')
    
    # ES 同步
    es_synced = Column(String(20), default='pending')
    es_synced_at = Column(DateTime(timezone=True))
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class SocialSentiment(Base):
    """社交舆情数据表"""
    __tablename__ = 'social_sentiment'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 平台信息
    platform = Column(String(50), nullable=False, comment='平台 (Twitter/Reddit/Weibo)')
    platform_id = Column(String(255), comment='平台内容ID')
    
    # 内容
    content = Column(Text, comment='内容文本')
    content_type = Column(String(30), comment='内容类型 (post/comment/article)')
    language = Column(String(10), default='en')
    
    # 作者
    author = Column(String(200), comment='作者')
    author_followers = Column(Integer, comment='粉丝数')
    author_verified = Column(String(20), comment='是否认证')
    
    # 关联标的
    symbols = Column(ARRAY(String), comment='提及的标的')
    hashtags = Column(ARRAY(String), comment='标签')
    
    # 情绪分析
    sentiment_score = Column(DECIMAL(6, 4), comment='情绪分数')
    sentiment_label = Column(String(20), comment='positive/negative/neutral')
    confidence = Column(DECIMAL(6, 4), comment='置信度')
    
    # 互动数据
    likes = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)
    
    # 时间
    posted_at = Column(DateTime(timezone=True), nullable=False)
    
    # ES 同步
    es_synced = Column(String(20), default='pending')
    es_synced_at = Column(DateTime(timezone=True))
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AlternativeSocialSentiment(Base):
    """另类社交舆情聚合表"""
    __tablename__ = 'alternative_social_sentiment'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    platform = Column(String(50), nullable=False)
    symbol = Column(String(100), nullable=False)
    
    mention_count = Column(Integer, default=0, comment='提及次数')
    sentiment_score = Column(DECIMAL(6, 4), comment='情绪分数')
    bullish_ratio = Column(DECIMAL(10, 4), comment='看涨比例')
    bearish_ratio = Column(DECIMAL(10, 4), comment='看跌比例')
    
    measured_at = Column(DateTime(timezone=True), nullable=False)
    
    source = Column(String(100))
    
    es_synced = Column(String(20), default='pending')
    es_synced_at = Column(DateTime(timezone=True))
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
