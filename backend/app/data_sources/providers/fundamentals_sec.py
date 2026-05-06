"""
SEC (Securities and Exchange Commission) 基本面数据源
SEC EDGAR API - SEC 文件、内部交易、机构持仓
API文档: https://www.sec.gov/developer
"""
import os
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


# SEC 常用文件类型
SEC_FORM_TYPES = {
    "10-K": "Annual Report",
    "10-Q": "Quarterly Report",
    "8-K": "Current Report",
    "DEF 14A": "Proxy Statement",
    "13F-HR": "Institutional Holdings",
    "4": "Insider Trading",
}


class SECProvider(BaseDataSource):
    """SEC EDGAR 基本面数据源"""

    name = "Fundamentals/SEC"
    BASE_URL = "https://www.sec.gov"
    DATA_URL = "https://data.sec.gov"

    def __init__(self):
        self._session = requests.Session()
        # SEC 要求特定请求头
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0 (contact@quantdinger.com)',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json'
        })
        # SEC 限流: 10次/秒
        self._limiter = RateLimiter(min_interval=0.1, jitter_min=0.02, jitter_max=0.08)
        self._cik_cache: Optional[Dict] = None
        self._cik_timestamp: float = 0

    def _normalize_cik(self, cik: Union[str, int]) -> str:
        """标准化 CIK 为 10 位格式"""
        return str(cik).strip().lstrip('0').zfill(10)

    def _get_company_tickers(self) -> Dict[str, Any]:
        """获取公司 ticker 到 CIK 的映射"""
        # 缓存1小时
        if self._cik_cache and (time.time() - self._cik_timestamp) < 3600:
            return self._cik_cache

        self._limiter.wait()
        url = f"{self.BASE_URL}/files/company_tickers.json"

        try:
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # 转换为便于查询的格式
            by_ticker = {}
            by_cik = {}
            for entry in data.values():
                ticker = entry.get('ticker', '').upper()
                cik = str(entry.get('cik_str', '')).zfill(10)
                title = entry.get('title', '')
                if ticker and cik:
                    by_ticker[ticker] = {'cik': cik, 'name': title}
                    by_cik[cik] = ticker

            self._cik_cache = {'by_ticker': by_ticker, 'by_cik': by_cik}
            self._cik_timestamp = time.time()
            return self._cik_cache

        except Exception as e:
            logger.error(f"[SEC] Failed to fetch company tickers: {e}")
            return {'by_ticker': {}, 'by_cik': {}}

    def get_cik(self, symbol: str) -> Optional[str]:
        """获取股票的 CIK"""
        tickers = self._get_company_tickers()
        info = tickers['by_ticker'].get(symbol.upper())
        return info['cik'] if info else None

    def get_symbol(self, cik: Union[str, int]) -> Optional[str]:
        """通过 CIK 获取 ticker"""
        tickers = self._get_company_tickers()
        return tickers['by_cik'].get(self._normalize_cik(cik))

    def get_submissions(self, cik: Union[str, int]) -> Dict[str, Any]:
        """获取公司提交文件列表"""
        normalized_cik = self._normalize_cik(cik)
        self._limiter.wait()

        url = f"{self.DATA_URL}/submissions/CIK{normalized_cik}.json"
        try:
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[SEC] Failed to fetch submissions: {e}")
            return {}

    def get_filings(
        self,
        symbol: Optional[str] = None,
        cik: Optional[Union[str, int]] = None,
        form_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """获取公司 SEC 文件列表"""
        if not cik and not symbol:
            return []

        if symbol and not cik:
            cik = self.get_cik(symbol)
            if not cik:
                return []

        data = self.get_submissions(cik)
        if not data or 'filings' not in data:
            return []

        recent = data['filings'].get('recent', {})
        if not recent:
            return []

        # 转换为列表
        forms = recent.get('form', [])
        dates = recent.get('filingDate', [])
        accession = recent.get('accessionNumber', [])
        docs = recent.get('primaryDocument', [])

        result = []
        for i in range(min(len(forms), limit * 2)):
            form = forms[i]
            if form_type and form.upper() != form_type.upper():
                continue

            result.append({
                'form': form,
                'date': dates[i] if i < len(dates) else None,
                'accession': accession[i] if i < len(accession) else None,
                'document': docs[i] if i < len(docs) else None,
                'url': self._build_filing_url(cik, accession[i] if i < len(accession) else '', docs[i] if i < len(docs) else ''),
            })

            if len(result) >= limit:
                break

        return result

    def _build_filing_url(self, cik: Union[str, int], accession: str, document: str) -> str:
        """构建 SEC 文件 URL"""
        cik_int = str(int(self._normalize_cik(cik)))
        accession_clean = accession.replace('-', '')
        return f"{self.BASE_URL}/Archives/edgar/data/{cik_int}/{accession_clean}/{document}"

    def get_company_facts(self, cik: Union[str, int]) -> Dict[str, Any]:
        """获取公司财务事实 (XBRL 数据)"""
        normalized_cik = self._normalize_cik(cik)
        self._limiter.wait()

        url = f"{self.DATA_URL}/api/xbrl/companyfacts/CIK{normalized_cik}.json"

        try:
            resp = self._session.get(url, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[SEC] Failed to fetch company facts: {e}")
            return {}

    def get_insider_trading(
        self,
        symbol: Optional[str] = None,
        cik: Optional[Union[str, int]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """获取内部人交易 (Form 4)"""
        return self.get_filings(symbol, cik, "4", limit)

    def get_institutional_holdings(
        self,
        symbol: Optional[str] = None,
        cik: Optional[Union[str, int]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """获取机构持仓 (Form 13F)"""
        return self.get_filings(symbol, cik, "13F-HR", limit)

    def get_annual_reports(
        self,
        symbol: Optional[str] = None,
        cik: Optional[Union[str, int]] = None,
        limit: int = 5
    ) -> List[Dict]:
        """获取年度报告 (10-K)"""
        return self.get_filings(symbol, cik, "10-K", limit)

    def get_quarterly_reports(
        self,
        symbol: Optional[str] = None,
        cik: Optional[Union[str, int]] = None,
        limit: int = 8
    ) -> List[Dict]:
        """获取季度报告 (10-Q)"""
        return self.get_filings(symbol, cik, "10-Q", limit)

    def get_key_indicators(self, symbol: str = "AAPL", limit: int = 10) -> Dict[str, Any]:
        """获取关键 SEC 指标"""
        cik = self.get_cik(symbol)
        if not cik:
            return {}

        cache_key = f"sec_indicators:{symbol}"
        facts = self.get_company_facts(cik)

        result = {}
        if facts and 'facts' in facts:
            us_gaap = facts['facts'].get('us-gaap', {})

            # 提取关键指标
            for metric, tags in {
                'revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
                'net_income': ['NetIncomeLoss'],
                'total_assets': ['Assets'],
                'total_liabilities': ['Liabilities'],
                'equity': ['StockholdersEquity', 'PartnersCapital'],
            }.items():
                for tag in tags:
                    if tag in us_gaap:
                        values = us_gaap[tag]
                        if isinstance(values, dict):
                            units = list(values.keys())
                            if units:
                                unit_data = values[units[0]]
                                if isinstance(unit_data, list) and unit_data:
                                    latest = max(unit_data, key=lambda x: x.get('end', ''))
                                    result[metric] = latest.get('val')
                                    break

        return result

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """SEC 不直接提供 K线"""
        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取股票信息"""
        cik = self.get_cik(symbol.upper())
        if cik:
            submissions = self.get_submissions(cik)
            recent = submissions.get('filings', {}).get('recent', {})
            if recent:
                return {
                    "last": 0,
                    "symbol": symbol.upper(),
                    "cik": cik,
                    "last_filing": recent.get('form', [None])[0] if recent.get('form') else None,
                    "last_filing_date": recent.get('filingDate', [None])[0] if recent.get('filingDate') else None,
                    "source": "SEC",
                }
        return {"last": 0, "symbol": symbol}