# QuantDinger Graphiti 第一批可开发任务拆分清单

> 版本：v1.0  
> 日期：2026-04  
> 状态：开发任务拆分 / Sprint 1 候选

---

## 1. 文档目标

本清单基于 `docs/GRAPHITI_IMPLEMENTATION_BLUEPRINT_CN.md`，将“第一批可开发任务”拆到文件级、类级、函数级、验收级，方便直接进入研发执行。

本批任务目标不是一次性完成全链路 Graphiti 改造，而是先打通最小可运行主链路：

```text
结构化数据落库
  -> CollectionRecord
  -> EpisodeBuilder
  -> GraphJob / GraphEpisode
  -> GraphPipeline
  -> GraphitiGateway(可降级)
  -> GraphContextBuilder(缓存优先)
  -> FastAnalysis / MarketDataCollector 接口接入
```

第一批任务聚焦：
- ORM 元数据补齐
- 统一采集记录模型
- Episode 与 GraphPipeline 基础链路
- 第一版 Repository
- 第一版 migration / SQL
- 第一版服务接入点
- 股票新闻链路 PoC 所需最小闭环

---

## 2. 第一批任务范围定义

### 2.1 本批必须完成

1. 建立统一采集记录 ORM 模型
2. 建立图谱任务 Repository
3. 建立 GraphPipeline 最小可运行链路
4. 建立第一版 migration / SQL 脚本
5. 让 `MarketDataCollector` 能输出可图谱化的标准对象
6. 让 `FastAnalysisService` 正式接入统一 `GraphContextBuilder`
7. 形成股票新闻 PoC 的任务入口

### 2.2 本批明确不做

- 不实现完整 Graphiti client 适配
- 不实现完整 Neo4j 查询体系
- 不实现三大领域全部入图逻辑
- 不实现全量回测因子生产
- 不实现前端展示
- 不实现完整审核后台

### 2.3 本批成功标准

满足以下任一链路可跑通即视为阶段完成：

**股票新闻 PoC：**
```text
新闻采集记录 -> CollectionRecord -> Episode -> GraphJob -> GraphitiGateway(真实或 mock) -> GraphContextBuilder -> FastAnalysis 可读取 graph_context
```

---

## 3. Sprint 1 建议拆分

| 任务组 | 优先级 | 目标 |
|------|------|------|
| A. ORM 与模型补齐 | P0 | 把数据库元数据结构补完整 |
| B. Repository 与持久化 | P0 | 提供统一读写接口 |
| C. Episode / GraphPipeline | P0 | 打通图谱任务主链路 |
| D. 服务接入 | P1 | 接到 `MarketDataCollector` / `FastAnalysisService` |
| E. Migration / SQL | P0 | 确保表结构可落地 |
| F. 股票新闻 PoC | P1 | 建立第一个可验收闭环 |

---

## 4. 任务组 A：ORM 与模型补齐

## A1. 新建 `app/models/collection.py`

### 目标
实现统一采集记录 ORM 模型，承接采集结果去重与图谱溯源。

### 文件
- `backend_api_python/app/models/collection.py`

### 需要新增类
- `CollectionRecord`

### 建议字段
- `id`
- `source`
- `data_type`
- `market`
- `symbol`
- `content_hash`
- `collected_at`
- `created_at`
- `updated_at`

### 验收标准
- 能被 SQLAlchemy 正常导入
- `content_hash` 唯一约束存在
- 可用于 DedupEngine 的数据库判重

---

## A2. 扩展 `app/models/graph_meta.py`

### 目标
补齐当前图谱元数据模型所缺字段/索引。

### 文件
- `backend_api_python/app/models/graph_meta.py`

### 关注点
- `GraphEpisode`
- `GraphJob`
- `GraphEntityRef`
- `GraphRelationSnapshot`
- `GraphFeatureDaily`

### 需要检查与补充
- 唯一约束是否齐全
- 常用索引是否齐全
- 字段命名与文档保持一致
- 类型是否兼容 PostgreSQL

### 验收标准
- 模型字段与蓝图中表设计一致度 > 90%
- 可直接用于后续 Alembic 迁移

---

## A3. 新建 `app/models/graph_domain.py`

### 目标
为三大领域的图谱特征表预留 ORM 模型。

### 文件
- `backend_api_python/app/models/graph_domain.py`

### 需要新增类
- `CompanyNarrativeFeature`
- `CryptoNarrativeFeature`
- `PolymarketMarketFeature`

### 验收标准
- 三个模型均可导入
- 均包含唯一键约束
- 字段名与文档保持一致

---

## 5. 任务组 B：Repository 与持久化

## B1. 新建 `app/database/repositories/base.py`

### 目标
提供统一 Repository 基类。

### 文件
- `backend_api_python/app/database/repositories/base.py`

### 需要实现类
- `BaseRepository`

### 建议方法
- `__init__(self, session)`
- `add(instance)`
- `add_all(instances)`
- `flush()`
- `commit()`
- `refresh(instance)`

### 验收标准
- 其他 Repository 可复用
- 不绑定具体业务表

---

## B2. 新建 `app/database/repositories/graph_repository.py`

### 目标
提供图谱元数据写入和查询接口。

### 文件
- `backend_api_python/app/database/repositories/graph_repository.py`

### 需要实现类
- `GraphRepository`

### 建议方法
- `create_episode(...)`
- `update_episode_status(episode_id, status, error_message=None)`
- `create_job(...)`
- `update_job_status(job_id, status, error_message=None)`
- `upsert_entity_ref(...)`
- `insert_feature_batch(features)`
- `get_features_by_symbol(market, symbol, start_date=None, end_date=None)`

### 验收标准
- 能完成 Episode / Job / Feature 的基本 CRUD
- 可被 GraphPipeline 调用

---

## B3. 新建 `app/database/repositories/market_repository.py`

### 目标
统一采集记录与结构化落库接口。

### 文件
- `backend_api_python/app/database/repositories/market_repository.py`

### 建议方法
- `create_collection_record(...)`
- `exists_by_content_hash(content_hash)`
- `save_financial_news(...)`
- `save_macro_indicator(...)`
- `save_market_price(...)`

### 验收标准
- DedupEngine 可复用该仓库
- 采集器后续可统一接 ORM

---

## 6. 任务组 C：Episode / GraphPipeline 主链路

## C1. 新建 `app/collectors/base.py`

### 目标
把文档中的 `CollectedItem` 正式落地为代码基础模型。

### 文件
- `backend_api_python/app/collectors/base.py`

### 需要实现
- `CollectedItem`
- `BaseCollector`

### 关键字段
- `source`
- `data_type`
- `market`
- `symbol`
- `raw_data`
- `normalized_data`
- `collected_at`
- `content_hash`
- `importance_score`
- `should_build_episode`
- `entity_keys`

### 验收标准
- 采集器输出可统一转成 `CollectedItem`
- 支持内容哈希生成

---

## C2. 新建 `app/collectors/graph_pipeline.py`

### 目标
打通 `EpisodeBuilder -> GraphRepository -> GraphitiGateway` 基础链路。

### 文件
- `backend_api_python/app/collectors/graph_pipeline.py`

### 需要实现类
- `GraphPipeline`

### 建议依赖注入
- `episode_builder`
- `graph_repository`
- `graphiti_gateway`
- `cache_manager`

### 建议方法
- `process_item(item)`
- `process_items(items)`
- `_should_skip_by_dedup(episode)`
- `_create_episode_record(episode)`
- `_create_job_record(episode_id)`
- `_dispatch_episode(episode, job_id)`
- `_mark_job_success(job_id)`
- `_mark_job_failed(job_id, error)`

### 验收标准
- 接收一个 `CollectedItem` 能创建 Episode 与 Job
- Graphiti 被禁用时不会抛致命错误
- Redis dedup key 能生效

---

## C3. 新建 `app/collectors/storage.py`

### 目标
提供采集结果落 PostgreSQL 的统一入口。

### 文件
- `backend_api_python/app/collectors/storage.py`

### 需要实现类
- `CollectorStorage`

### 建议方法
- `save_item(item)`
- `save_items(items)`
- `save_collection_record(item)`
- `save_domain_payload(item)`

### 验收标准
- 至少支持保存 `CollectionRecord`
- 后续可扩展保存领域表

---

## C4. 新建 `app/collectors/dedup.py`

### 目标
将当前文档方案落地成可复用去重模块。

### 文件
- `backend_api_python/app/collectors/dedup.py`

### 需要实现类
- `DedupEngine`

### 建议方法
- `filter(items)`
- `_in_memory_seen(content_hash)`
- `_in_db(content_hash)`

### 验收标准
- 内存去重 + DB 去重都可用
- 可与 `CollectionRecord` 协同工作

---

## 7. 任务组 D：服务接入

## D1. 改造 `app/services/market_data_collector.py`

### 目标
增加标准化输出适配能力，为后续 Collector 化做准备。

### 文件
- `backend_api_python/app/services/market_data_collector.py`

### 建议新增方法
- `_to_collected_item(...)`
- `_build_news_collected_items(...)`
- `_build_macro_collected_items(...)`
- `_build_polymarket_collected_items(...)`

### 目标行为
- 先不改现有 `collect_all()` 返回结构
- 额外提供“可图谱化 item 列表”输出能力

### 验收标准
- 至少可对股票新闻构造 `CollectedItem`
- 不影响现有 API 行为

---

## D2. 改造 `app/services/fast_analysis.py`

### 目标
统一接入新的 `GraphContextBuilder` 和缓存化图谱上下文。

### 文件
- `backend_api_python/app/services/fast_analysis.py`

### 需要检查/修改点
- `_get_graph_builder()` 的初始化逻辑
- `_collect_market_data()` 是否支持 `include_graph_context`
- Prompt 注入是否使用统一 `format_graph_context_for_llm()`

### 验收标准
- `GRAPHITI_ENABLED=true` 时可注入 graph_context
- 失败时自动降级为空上下文

---

## D3. 改造 `app/graph/context_builder.py`

### 目标
从“空骨架”升级为“缓存优先 + 查询占位”版本。

### 文件
- `backend_api_python/app/graph/context_builder.py`

### 需要补充方法
- `_build_fresh(market, symbol)`
- `_get_related_assets(...)`
- `_get_stock_context(...)`
- `_get_crypto_context(...)`
- `_get_polymarket_context(...)`

### 本批要求
- 不要求完整 GraphRAG
- 允许先返回 mock / placeholder / 空数组
- 但接口结构必须稳定

### 验收标准
- 上下文结构固定
- Redis 缓存读写正常
- 不阻塞 AI 主链路

---

## 8. 任务组 E：Migration / SQL

## E1. 新建第一版 SQL migration 草案

### 目标
先以 SQL 或 Python migration 形式，把最关键的表创建出来。

### 文件候选
- `backend_api_python/migrations/graphiti_phase1.sql`
或
- `backend_api_python/migrations/versions/003_add_graph_meta_tables.py`

### 本批必须包含的表
- `qd_collection_records`
- `qd_graph_episodes`
- `qd_graph_jobs`
- `qd_graph_entity_refs`
- `qd_graph_relation_snapshots`
- `qd_graph_feature_daily`

### 验收标准
- SQL 语法可审阅
- 字段与 ORM 模型一致
- 唯一键与索引完整

---

## E2. 补 Alembic 骨架文件

### 目标
为后续正式迁移体系预留目录和入口。

### 文件
- `backend_api_python/migrations/alembic.ini`
- `backend_api_python/migrations/env.py`
- `backend_api_python/migrations/versions/__init__.py`

### 验收标准
- 目录结构具备
- 后续可直接接 Alembic 初始化

---

## 9. 任务组 F：股票新闻 PoC

## F1. 建立股票新闻 -> Episode PoC

### 目标
用股票新闻作为第一条打通链路。

### 输入
- `finnhub_news`
- `symbol=NVDA` 或 `AAPL`

### 流程
1. 新闻被采集
2. 转成 `CollectedItem`
3. 进入 `CollectorStorage`
4. 生成 `GraphEpisode`
5. 创建 `GraphJob`
6. 交给 `GraphPipeline`
7. `GraphitiGateway` 返回成功/降级状态
8. `FastAnalysisService` 可读取 `graph_context`

### 验收标准
- 至少能在数据库中看到：
  - 一条 `CollectionRecord`
  - 一条 `GraphEpisode`
  - 一条 `GraphJob`
- 主分析流程不报错

---

## 10. 文件级任务总表

| 文件 | 操作 | 优先级 |
|------|------|--------|
| `app/models/collection.py` | 新建 | P0 |
| `app/models/graph_domain.py` | 新建 | P1 |
| `app/database/repositories/base.py` | 新建 | P0 |
| `app/database/repositories/graph_repository.py` | 新建 | P0 |
| `app/database/repositories/market_repository.py` | 新建 | P0 |
| `app/collectors/base.py` | 新建 | P0 |
| `app/collectors/dedup.py` | 新建 | P0 |
| `app/collectors/storage.py` | 新建 | P0 |
| `app/collectors/graph_pipeline.py` | 新建 | P0 |
| `app/services/market_data_collector.py` | 修改 | P1 |
| `app/services/fast_analysis.py` | 修改 | P1 |
| `app/graph/context_builder.py` | 修改 | P1 |
| `migrations/graphiti_phase1.sql` 或 Alembic 文件 | 新建 | P0 |
| `migrations/alembic.ini` | 新建 | P1 |
| `migrations/env.py` | 新建 | P1 |

---

## 11. 建议开发顺序

### Day 1-2
- A1 `collection.py`
- B1 `base.py`
- B2 `graph_repository.py`
- C1 `collectors/base.py`

### Day 3-4
- C3 `storage.py`
- C4 `dedup.py`
- C2 `graph_pipeline.py`

### Day 5
- E1 第一版 migration / SQL
- E2 Alembic 骨架

### Day 6-7
- D1 `market_data_collector.py` 适配
- D2 `fast_analysis.py` 接入
- D3 `context_builder.py` 稳定化

### Day 8
- F1 股票新闻 PoC 联调
- 修正数据流、异常处理、降级路径

---

## 12. 每项任务的 Definition of Done

每个任务完成时必须满足：

1. 文件存在且可导入
2. 不破坏现有主链路
3. 接口命名与蓝图一致或兼容
4. 失败路径有降级处理
5. 已做最小范围检查
6. 关键日志可观测

---

## 13. 推荐下一步执行方式

建议接下来的开发节奏：

### 路径 A：我继续直接落代码
按以下顺序连续实现：
1. `collection.py`
2. `graph_repository.py`
3. `collectors/base.py`
4. `dedup.py`
5. `storage.py`
6. `graph_pipeline.py`
7. phase1 migration SQL

### 路径 B：先生成任务卡片
把上面的每项任务拆成更细的：
- 输入
- 输出
- 文件修改点
- 验收语句
- 风险点

如果你要我继续，我建议直接走路径 A，我可以开始把这第一批 P0 代码逐个落下去。

---

*本文件用于把蓝图转换成可开发任务，后续进入实际编码时，应优先以本清单作为 Sprint 任务来源。*
