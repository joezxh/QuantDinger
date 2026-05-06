"""
证券基础数据模型（公司/股东/机构持仓/内部人交易）
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, DECIMAL, Integer, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base


class SecurityCompany(Base):
    """上市公司基本信息表"""
    __tablename__ = 'security_companies'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 基本信息
    market = Column(String(50), nullable=False, comment='USStock/CNStock/HKStock')
    ticker = Column(String(50), nullable=False, comment='股票代码')
    company_name = Column(String(500), nullable=False, comment='公司名称')
    company_name_en = Column(String(500), comment='英文名称')
    
    # 公司信息
    legal_name = Column(String(500), comment='法定名称')
    short_name = Column(String(200), comment='简称')
    website = Column(String(500), comment='官网')
    description = Column(Text, comment='公司简介')
    description_en = Column(Text, comment='英文简介')
    
    # 行业分类
    sector = Column(String(100), comment='行业')
    industry = Column(String(100), comment='细分行业')
    gics_sector = Column(String(100), comment='GICS行业分类')
    gics_industry = Column(String(100), comment='GICS细分')
    
    # 上市信息
    ipo_date = Column(Date, comment='上市日期')
    exchange = Column(String(50), comment='交易所')
    listing_status = Column(String(30), default='active', comment='active/delisted/suspended')
    
    # 联系信息
    headquarters = Column(String(200), comment='总部所在地')
    country = Column(String(50), comment='国家')
    employees = Column(Integer, comment='员工数')
    
    # ES 同步
    es_synced = Column(String(20), default='pending')
    es_synced_at = Column(DateTime(timezone=True))
    
    # 元数据
    payload_json = Column(JSONB, comment='原始完整数据')
    last_synced_at = Column(DateTime(timezone=True), comment='最后同步时间')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class SecurityShareholder(Base):
    """股东信息表"""
    __tablename__ = 'security_shareholders'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 关联信息
    company_id = Column(BigInteger, ForeignKey('security_companies.id'), comment='关联公司')
    market = Column(String(50), nullable=False)
    ticker = Column(String(50), nullable=False)
    
    # 股东信息
    shareholder_name = Column(String(500), nullable=False, comment='股东名称')
    shareholder_type = Column(String(50), comment='individual/institution/corporate/government')
    
    # 持股信息
    shares_held = Column(DECIMAL(24, 8), comment='持股数量')
    shares_percent = Column(DECIMAL(10, 4), comment='持股比例(%)')
    market_value = Column(DECIMAL(24, 8), comment='持股市值')
    
    # 机构信息
    institution_type = Column(String(50), comment='fund/insurance/bank/other')
    is_insider = Column(Boolean, default=False, comment='是否内部人')
    
    # 时间信息
    report_date = Column(Date, nullable=False, comment='报告日期')
    period_type = Column(String(20), comment='quarterly/annual')
    
    # 变动信息
    shares_change = Column(DECIMAL(24, 8), comment='持股变动')
    shares_change_percent = Column(DECIMAL(10, 4), comment='变动比例')
    
    # 实体关联（去重）
    entity_id = Column(BigInteger, comment='关联 entity_financial_institutions.id')
    
    # 来源
    source = Column(String(100), comment='数据来源')
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SecurityInstitutionalHolding(Base):
    """机构持仓明细表"""
    __tablename__ = 'security_institutional_holdings'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    company_id = Column(BigInteger, ForeignKey('security_companies.id'))
    market = Column(String(50), nullable=False)
    ticker = Column(String(50), nullable=False)
    
    # 机构信息
    institution_name = Column(String(500), nullable=False)
    institution_type = Column(String(50))
    cik = Column(String(20), comment='CIK编号')
    
    # 持仓信息
    shares_held = Column(DECIMAL(24, 8), nullable=False)
    shares_percent = Column(DECIMAL(10, 4))
    market_value = Column(DECIMAL(24, 8))
    
    # 排名
    holder_rank = Column(Integer, comment='股东排名')
    
    # 时间
    report_date = Column(Date, nullable=False)
    filing_date = Column(Date, comment='提交日期')
    
    # 实体关联（去重）
    entity_id = Column(BigInteger, comment='关联 entity_financial_institutions.id')
    
    source = Column(String(100), default='13F')
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SecurityInsiderTrade(Base):
    """公司内部人交易表"""
    __tablename__ = 'security_insider_trades'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    company_id = Column(BigInteger, ForeignKey('security_companies.id'))
    market = Column(String(50), nullable=False)
    ticker = Column(String(50), nullable=False)
    
    # 内部人信息
    insider_name = Column(String(500), nullable=False)
    insider_title = Column(String(200), comment='职位')
    is_officer = Column(Boolean, default=False)
    is_director = Column(Boolean, default=False)
    is_ten_percent_owner = Column(Boolean, default=False)
    
    # 交易信息
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(String(50), comment='purchase/sale/award/exercise')
    
    # 交易数量
    shares = Column(Integer, nullable=False, comment='交易股数')
    price_per_share = Column(DECIMAL(10, 4), comment='每股价格')
    total_value = Column(DECIMAL(24, 8), comment='总价值')
    
    # 持股变化
    shares_owned_before = Column(Integer)
    shares_owned_after = Column(Integer)
    
    # 元数据
    filing_date = Column(Date, comment='提交日期')
    sec_form_type = Column(String(20), comment='Form 4/Form 5')
    sec_filing_url = Column(String(1000))
    
    payload_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
