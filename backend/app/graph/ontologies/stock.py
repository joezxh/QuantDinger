"""Stock market ontology — entities and relationships for equity domain."""
from typing import Optional

from pydantic import Field

try:
    from graphiti_core.nodes import Entity
except ImportError:
    Entity = object  # type: ignore[misc,assignment]


class Company(Entity):  # type: ignore[misc,valid-type]
    """Publicly traded company."""

    ticker: str = Field(..., description="证券代码")
    name: Optional[str] = Field(None, description="公司名称")
    sector: Optional[str] = Field(None, description="所属行业")
    market_cap: Optional[float] = Field(None, description="市值")
    exchange: Optional[str] = Field(None, description="交易所")


class Executive(Entity):  # type: ignore[misc,valid-type]
    """Corporate executive or board member."""

    name: str = Field(..., description="姓名")
    role: Optional[str] = Field(None, description="职位")
    company_ticker: Optional[str] = Field(None, description="所属公司代码")


class Institution(Entity):  # type: ignore[misc,valid-type]
    """Financial institution, fund, or major shareholder."""

    name: str = Field(..., description="机构名称")
    type: Optional[str] = Field(None, description="机构类型(基金/银行/保险/主权基金)")
    aum_billion: Optional[float] = Field(None, description="资产管理规模(十亿美元)")
