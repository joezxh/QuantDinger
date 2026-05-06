# 搜索引擎和 AI 数据源配置指南

## 概述

本文档详细介绍新添加的 7 个搜索引擎和 AI 数据源的配置信息，包括博查(Bocha)、数眼智能(SHUYAN)、安思派(ANSPIRE)、Firecrawl、Google、Baidu、Bing。

这些数据源已统一纳入 `data_source_meta.py` 数据库模型管理，支持在前端控制台进行完整的配置管理。

---

## 数据源清单

### 1. Bocha 博查 AI 搜索

**数据源代码**: `search_bocha`

**基本信息**:
- 名称: Bocha AI Search (博查)
- 类别: News, Alternative
- 层: data_source
- 状态: 启用

**API 配置**:
```json
{
  "api_key_env": "BOCHA_API_KEY",
  "api_key_required": true,
  "base_url": "https://api.bochaai.com/v1",
  "timeout_sec": 15,
  "rate_limit_per_min": 60,
  "features": ["web_search", "news_search", "knowledge_graph"]
}
```

**限流配置**:
- 策略: token_bucket
- 速率: 60 次/分钟
- 突发容量: 60
- 最大并发: 10

**功能特性**:
- ✅ 网页搜索
- ✅ 新闻搜索
- ✅ 知识图谱
- ✅ 中文语义理解

**使用场景**:
- 中文新闻检索
- 行业知识查询
- 语义搜索

---

### 2. SHUYAN 数眼智能

**数据源代码**: `search_shuyan`

**基本信息**:
- 名称: SHUYAN Intelligence (数眼智能)
- 类别: News, Alternative
- 层: data_source
- 状态: 启用

**API 配置**:
```json
{
  "api_key_env": "SHUYAN_API_KEY",
  "api_key_required": true,
  "base_url": "https://api.shuyan.com/v1",
  "timeout_sec": 15,
  "rate_limit_per_min": 50,
  "features": ["financial_news", "data_analysis", "sentiment"]
}
```

**限流配置**:
- 策略: token_bucket
- 速率: 50 次/分钟
- 突发容量: 50
- 最大并发: 10

**功能特性**:
- ✅ 财经新闻
- ✅ 数据分析
- ✅ 情感分析

**使用场景**:
- 财经资讯获取
- 市场情绪分析
- 数据洞察

---

### 3. ANSPIRE 安思派

**数据源代码**: `search_anspire`

**基本信息**:
- 名称: ANSPIRE Data Service (安思派)
- 类别: Fundamentals, News, Alternative
- 层: data_source
- 状态: 启用

**API 配置**:
```json
{
  "api_key_env": "ANSPIRE_API_KEY",
  "api_key_required": true,
  "base_url": "https://api.anspire.com/v1",
  "timeout_sec": 20,
  "rate_limit_per_min": 40,
  "features": ["company_data", "industry_analysis", "market_research"]
}
```

**限流配置**:
- 策略: token_bucket
- 速率: 40 次/分钟
- 突发容量: 40
- 最大并发: 8

**功能特性**:
- ✅ 企业数据
- ✅ 行业分析
- ✅ 市场调研

**使用场景**:
- 企业基本面分析
- 行业研究报告
- 市场趋势调研

---

### 4. Firecrawl 私有化部署

**数据源代码**: `search_firecrawl`

**基本信息**:
- 名称: Firecrawl (私有化部署)
- 类别: News, Alternative
- 层: data_source
- 状态: 启用

**API 配置**:
```json
{
  "api_key_env": "FIRECRAWL_API_KEY",
  "api_key_required": true,
  "base_url": "http://localhost:3002",
  "timeout_sec": 30,
  "rate_limit_per_min": 30,
  "features": ["web_scraping", "crawl", "extract", "markdown"],
  "self_hosted": true
}
```

**限流配置**:
- 策略: token_bucket
- 速率: 30 次/分钟
- 突发容量: 30
- 最大并发: 5
- 错误降速: 启用
- 错误阈值: 3

**功能特性**:
- ✅ 网页爬取
- ✅ 内容提取
- ✅ Markdown 转换
- ✅ 私有化部署

**使用场景**:
- 自定义网页抓取
- 数据采集
- 内容结构化

**部署说明**:
```bash
# Docker 部署示例
docker run -d \
  -p 3002:3002 \
  -e FIRECRAWL_API_KEY=your_key \
  --name firecrawl \
  mendableai/firecrawl
```

---

### 5. Google Search API

**数据源代码**: `search_google`

**基本信息**:
- 名称: Google Search API
- 类别: News, Alternative
- 层: data_source
- 状态: 启用

**API 配置**:
```json
{
  "api_key_env": "GOOGLE_SEARCH_API_KEY",
  "api_key_required": true,
  "base_url": "https://www.googleapis.com/customsearch/v1",
  "timeout_sec": 10,
  "rate_limit_per_min": 100,
  "cx_env": "GOOGLE_SEARCH_CX",
  "features": ["web_search", "news_search"]
}
```

**限流配置**:
- 策略: token_bucket
- 速率: 100 次/分钟
- 突发容量: 100
- 最大并发: 15

**功能特性**:
- ✅ 网页搜索
- ✅ 新闻搜索
- ✅ 全球内容覆盖

**使用场景**:
- 全球新闻检索
- 多语言搜索
- 广泛内容查询

**配置要求**:
1. 申请 Google Cloud API Key
2. 创建 Custom Search Engine (CSE)
3. 获取 Search Engine ID (CX)

---

### 6. Baidu 百度搜索

**数据源代码**: `search_baidu`

**基本信息**:
- 名称: Baidu Search API (百度)
- 类别: News, Alternative
- 层: data_source
- 状态: 启用

**API 配置**:
```json
{
  "api_key_env": "BAIDU_API_KEY",
  "api_key_required": true,
  "base_url": "https://aip.baidubce.com/rest/2.0",
  "timeout_sec": 10,
  "rate_limit_per_min": 80,
  "features": ["web_search", "news_search", "chinese_content"]
}
```

**限流配置**:
- 策略: token_bucket
- 速率: 80 次/分钟
- 突发容量: 80
- 最大并发: 12

**功能特性**:
- ✅ 网页搜索
- ✅ 新闻搜索
- ✅ 中文内容覆盖全面

**使用场景**:
- 中文新闻检索
- 国内市场调研
- 中文内容分析

---

### 7. Bing 必应搜索

**数据源代码**: `search_bing`

**基本信息**:
- 名称: Bing Search API (必应)
- 类别: News, Alternative
- 层: data_source
- 状态: 启用

**API 配置**:
```json
{
  "api_key_env": "BING_SEARCH_API_KEY",
  "api_key_required": true,
  "base_url": "https://api.bing.microsoft.com/v7.0",
  "timeout_sec": 10,
  "rate_limit_per_min": 100,
  "features": ["web_search", "news_search", "image_search"]
}
```

**限流配置**:
- 策略: token_bucket
- 速率: 100 次/分钟
- 突发容量: 100
- 最大并发: 15

**功能特性**:
- ✅ 网页搜索
- ✅ 新闻搜索
- ✅ 图片搜索
- ✅ 全球内容覆盖

**使用场景**:
- 全球新闻检索
- 多语言搜索
- 图片资源查询

---

## 数据源对比

| 数据源 | 中文支持 | 全球覆盖 | 专业性 | 价格 | 推荐场景 |
|--------|---------|---------|--------|------|---------|
| 博查 Bocha | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | 中文语义搜索 |
| 数眼 SHUYAN | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中高 | 财经数据分析 |
| 安思派 ANSPIRE | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高 | 专业市场研究 |
| Firecrawl | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 低(自部署) | 自定义数据采集 |
| Google | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 中 | 全球内容搜索 |
| Baidu | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | 中 | 中文内容搜索 |
| Bing | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 中 | 多语言搜索 |

---

## 前端配置管理

### 1. 查看数据源配置

访问路径: `/data-source`

在数据源列表中搜索:
- `search_bocha` - 博查
- `search_shuyan` - 数眼智能
- `search_anspire` - 安思派
- `search_firecrawl` - Firecrawl
- `search_google` - Google
- `search_baidu` - 百度
- `search_bing` - 必应

### 2. 配置 API 密钥

1. 在数据源列表中点击 **"密钥管理"**
2. 点击 **"添加密钥"**
3. 填写密钥信息:
   - 密钥类型: 公共密钥
   - 密钥别名: 如 "Bocha API Key #1"
   - 密钥值: 从服务商获取的 API Key
   - 权重: 1-100
   - 日调用限制: 根据套餐设置

### 3. 调整限流配置

1. 在数据源列表中点击 **"限流配置"**
2. 修改限流参数:
   - 限流策略: token_bucket (推荐)
   - 每周期请求数: 根据 API 套餐调整
   - 周期长度: 60 秒
   - 突发容量: 通常等于速率
   - 最大并发: 5-15

### 4. 监控健康状态

1. 访问 `/data-source/health`
2. 点击 **"全面健康检查"**
3. 查看各数据源的健康状态和响应时间

---

## 环境变量配置

在 `.env` 文件中添加以下配置（可选，推荐在数据库中配置）:

```bash
# 搜索引擎 API Keys
BOCHA_API_KEY=your_bocha_api_key
SHUYAN_API_KEY=your_shuyan_api_key
ANSPIRE_API_KEY=your_anspire_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_CX=your_google_cx_id
BAIDU_API_KEY=your_baidu_api_key
BING_SEARCH_API_KEY=your_bing_api_key
```

---

## 数据库初始化

运行 SQL 迁移脚本:

```bash
# PostgreSQL
psql -U your_user -d your_database -f init_data_sources_v4.sql
```

这将:
1. 创建 7 个数据源配置
2. 创建对应的限流配置
3. 初始化健康检查记录

---

## 优先级路由策略

搜索引擎类别的数据源优先级设置:

```
Google (80) > Bing (75) > Baidu (70) > Bocha (65) > SHUYAN (60) > Firecrawl (50)
```

**路由逻辑**:
1. 优先使用 Google 和 Bing（全球覆盖）
2. 中文内容优先 Baidu 和 Bocha
3. 专业数据使用 SHUYAN 和 ANSPIRE
4. 自定义抓取使用 Firecrawl

---

## 使用示例

### Python 代码示例

```python
from app.data_sources.config_loader import DataSourceConfigLoader

# 加载数据源配置
loader = DataSourceConfigLoader()

# 获取博查配置
bocha_config = loader.load_source_config('search_bocha')

# 获取 API Key
bocha_api_key = loader.get_api_key('search_bocha')

# 使用配置发起请求
import requests
response = requests.get(
    f"{bocha_config['config_json']['base_url']}/web-search",
    headers={"Authorization": f"Bearer {bocha_api_key}"},
    params={"q": "AI技术发展趋势", "limit": 10}
)
```

### 前端调用示例

```javascript
// 获取数据源列表
const response = await fetch('/api/data-sources/');
const data = await response.json();

// 过滤搜索引擎数据源
const searchSources = data.data_sources.filter(
  source => source.source_code.startsWith('search_')
);

// 检查健康状态
const healthResponse = await fetch('/api/data-sources/health/search_google');
const health = await healthResponse.json();
```

---

## 注意事项

### 1. API Key 安全
- ✅ 使用 AES-256-GCM 加密存储
- ✅ 不要在代码中硬编码
- ✅ 定期轮换密钥
- ✅ 监控使用统计

### 2. 限流管理
- ✅ 根据 API 套餐设置合理的限流参数
- ✅ 启用错误降速避免被封禁
- ✅ 定期检查限流统计
- ✅ 配置多个密钥实现负载均衡

### 3. 健康监控
- ✅ 定期进行健康检查
- ✅ 关注响应时间变化
- ✅ 及时处理异常数据源
- ✅ 设置告警通知

### 4. 成本控制
- ✅ 监控 API 调用次数
- ✅ 设置日调用限制
- ✅ 优先使用免费/低成本数据源
- ✅ 缓存常用查询结果

---

## 故障排查

### 问题 1: 健康检查失败

**可能原因**:
- API Key 无效或过期
- 网络连接问题
- 服务商会限

**解决方案**:
1. 检查 API Key 是否正确
2. 测试网络连接
3. 查看服务商状态页面
4. 检查限流配置

### 问题 2: 响应时间过长

**可能原因**:
- 服务商响应慢
- 网络延迟
- 并发请求过多

**解决方案**:
1. 调整超时设置
2. 降低并发数
3. 启用缓存
4. 切换到备用数据源

### 问题 3: 触发限流

**可能原因**:
- 限流参数设置过高
- 调用频率过快
- 多个密钥共享配额

**解决方案**:
1. 降低限流速率
2. 增加周期长度
3. 添加更多 API Key
4. 启用请求队列

---

## 更新日志

### v1.0.0 (2026-05-03)
- ✅ 添加 7 个搜索引擎和 AI 数据源
- ✅ 完整的数据源配置
- ✅ 限流配置初始化
- ✅ 健康检查支持
- ✅ 前端管理界面集成

---

## 相关文档

- [数据源管理使用指南](../DATA_SOURCE_MANAGER_GUIDE.md)
- [数据源配置迁移总结](../DATA_SOURCE_MANAGEMENT_SUMMARY.md)
- [快速启动指南](../QUICK_START.md)

---

## 联系支持

如有问题或需要帮助，请联系开发团队或查看官方文档。
