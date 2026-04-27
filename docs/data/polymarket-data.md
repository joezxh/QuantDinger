
QuantDinger 中获取 Polymarket 预测市场数据使用的是 **Python 标准库 `requests`**，没有依赖专门的 Polymarket SDK。调用的是 Polymarket 官方提供的 **3 个公开 REST API 端点**，完全免费且**无需 API Key**。

## 使用的 API 端点

| API | 基础地址 | 用途 |
|-----|----------|------|
| **Gamma API** | `https://gamma-api.polymarket.com` | 市场列表、事件、标签、搜索 |
| **Data API** | `https://data-api.polymarket.com` | 交易记录、用户持仓、活动 |
| **CLOB API** | `https://clob.polymarket.com` | 订单簿、实时价格 |

> 这三个端点均为 Polymarket 官方公开接口，不需要认证即可访问。

## 数据获取流程

代码位于 [`backend/app/data_sources/polymarket.py`](d:/projects/QuantDinger/backend/app/data_sources/polymarket.py)：

```
┌─────────────────────────────────────────────────────────────┐
│  1. 初始化 Session                                           │
│     - requests.Session()                                      │
│     - 设置 User-Agent + Accept: application/json              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ 获取热门市场   │    │ 获取市场详情   │    │ 搜索市场       │
│ get_trending  │    │ get_market_   │    │ search_markets│
│ _markets()    │    │ details()     │    │ ()            │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
              ┌────────────────────────────┐
              │  2. 优先读取数据库缓存        │
              │     qd_polymarket_markets    │
              │     (5 分钟 TTL 缓存策略)     │
              └─────────────┬──────────────┘
                            │
              ┌─────────────┴──────────────┐
              │ 缓存命中 → 直接返回缓存数据   │
              │ 缓存未命中 → 调用 API 获取    │
              └─────────────┬──────────────┘
                            ▼
              ┌────────────────────────────┐
              │  3. 调用 Gamma API          │
              │  GET /events?active=true    │
              │       &closed=false         │
              │       &limit=100            │
              └─────────────┬──────────────┘
                            ▼
              ┌────────────────────────────┐
              │  4. 解析 & 标准化数据        │
              │     _parse_gamma_events()   │
              │     提取市场ID、问题、概率    │
              │     交易量、流动性、状态等    │
              └─────────────┬──────────────┘
                            ▼
              ┌────────────────────────────┐
              │  5. 后处理                   │
              │     - 按 market_id 去重      │
              │     - 按 volume_24h 降序排序 │
              └─────────────┬──────────────┘
                            ▼
              ┌────────────────────────────┐
              │  6. 写入数据库缓存            │
              │     _save_markets_to_db()   │
              │     表: qd_polymarket_markets│
              └────────────────────────────┘
```

## 核心方法说明

| 方法 | 功能 | 对应 API |
|------|------|----------|
| `_fetch_from_gamma_api()` | 批量获取活跃事件列表 | `GET /gamma-api/events` |
| `_fetch_market_by_slug()` | 通过 slug 精确查询（最高效） | `GET /gamma-api/markets?slug=` |
| `_fetch_market_from_api()` | 通过 id 或 slug 获取单个市场 | `GET /gamma-api/markets` |
| `search_markets()` | 关键词搜索，支持本地缓存或实时 API | 组合调用 |
| `_save_markets_to_db()` | 缓存到 PostgreSQL | `qd_polymarket_markets` |

## 搜索/分析时的匹配策略

当用户输入链接或标题时，系统会按以下优先级匹配：

1. **链接解析** — 从 `polymarket.com/event/{slug}` 提取 slug
2. **Slug 精确查询** — 直接调用 `/markets?slug=xxx`（最高效）
3. **数字 ID 匹配** — 纯数字则匹配 `market_id`
4. **关键词模糊匹配** — 提取关键词（过滤停用词），在问题标题中匹配，阈值 40%
5. **分页获取兜底** — 最多拉取 3000 个市场做本地过滤

如需接入其他预测市场（如 Manifold Markets），同一文件内也预留了扩展结构。