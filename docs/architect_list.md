---

## 已生成的技术方案文档（共 8 个）


| 文档                                      | 内容                                                                                                                     | 规模    |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----- |
| `ARCHITECTURE_REFORM_MASTER_PLAN_CN.md` | **总体架构改造方案**：背景、现状分析、目标架构全景、七大模块概览、技术选型、路线图、风险评估、安全设计                                                                  | 262 行 |
| `ORM_MIGRATION_PLAN_CN.md`              | **SQLAlchemy ORM 重构**：问题分析、模型层设计（User/Strategy/MarketPrice/Kline）、Session 管理、Alembic 迁移、双轨并行策略、回滚方案                    | 428 行 |
| `UNIFIED_DATA_COLLECTION_CN.md`         | **统一数据采集系统**：BaseCollector 抽象接口、7类数据源采集器（Crypto/Stock/Forex/Macro/News/Polymarket）、去重引擎、APScheduler 调度、Dify Webhook 触发 | 254 行 |
| `KNOWLEDGE_GRAPH_INFRA_CN.md`           | **Neo4j 知识图谱基础设施**：Docker Compose 集成、节点/关系类型设计、索引策略、数据导入 Pipeline、图查询 API                                              | 285 行 |
| `GRAPH_POLYMARKET_CN.md`                | **预测市场关系图谱**：Polymarket Data API 采集、用户账号/交易记录、影响力评分 Cypher 查询、聪明钱识别                                                    | 209 行 |
| `GRAPH_FINANCIAL_MARKET_CN.md`          | **金融市场实体关系图谱**：机构持股采集（Finnhub）、公司/股东/新闻节点、共同股东分析、LLM 实体提取                                                              | 280 行 |
| `GRAPH_CRYPTO_ACCOUNT_CN.md`            | **加密账号关系图谱**：链上地址采集（Etherscan）、KOL/鲸鱼节点、资金流向追踪、地址聚类分析                                                                  | 296 行 |
| `AI_ANALYSIS_ENHANCEMENT_CN.md`         | **AI 分析增强**：GraphContextBuilder 图谱上下文注入、集成到 FastAnalysis、事件影响链分析、聪明钱信号聚合                                               | 341 行 |





1.D:\projects\QuantDinger\docs\artice\AI_ANALYSIS_ENHANCEMENT_CN.md
2.D:\projects\QuantDinger\docs\artice\ARCHITECTURE_REFORM_MASTER_PLAN_CN.md
3.D:\projects\QuantDinger\docs\artice\GRAPH_CRYPTO_ACCOUNT_CN.md
4.D:\projects\QuantDinger\docs\artice\GRAPH_FINANCIAL_MARKET_CN.md
5.D:\projects\QuantDinger\docs\artice\GRAPH_POLYMARKET_CN.md
6.D:\projects\QuantDinger\docs\artice\graphiti-crypto.md
7.D:\projects\QuantDinger\docs\artice\graphiti-polymarket.md
8.D:\projects\QuantDinger\docs\artice\graphiti-stock.md
9.D:\projects\QuantDinger\docs\artice\KNOWLEDGE_GRAPH_INFRA_CN.md
10.D:\projects\QuantDinger\docs\artice\ORM_MIGRATION_PLAN_CN.md
11.D:\projects\QuantDinger\docs\artice\UNIFIED_DATA_COLLECTION_CN.md

根据以下具体要求修改QuantDinger架构改造方案:
1.**ORM改造**:将原代码中所有直接使用裸SQL实现的逻辑全部改为SQLAlchemy ORM实现。请遍历整个项目，整理出所有还需要改造为ORM的部分，并制定完整的迁移计划。
2.**ORM迁移策略*:统一使用一个初始的init.sq文件，通过Alembic合并为一个初始化版本，该版本需包含所有现有表结构。清理掉其他多余的版本文件，确保迁移路径清晰简洁。
3.**Dify工作流集成*:QuantDinger项目已有私有化部署的Dify，不要在graphit数据生成阶段使用，主要在AI分析模块中使用。Al分析需要既保留现有的分析pipeline，又增加可选择的Dify工作流分析选项。其他数据分析保持不变。需要开发一个工作流管理模块来管理Dif工作流，保存Dif调用参数如apikey等，按照code编码引用时调用。提供流式与段式两种调用方式，支持Dify的各种工作流类型。
4.**neomodel OGM排除**:不引|入neomodel对象图映射框架。
5.*Graphit集成方式*:Graphit实体代码从IDAprojectslgithubgraphit]复制，不独立启动一个服务，而是作为QuantDinger的一部分，与QuantDinger服务一起启动。调用Graphiti时使用自有model import实现。
6.**API路径统一**:接受当前建议的API路径统一方案。
7.**实施工期合理性**:确保实施工期安排合理可行。
8.*Graphit启用时机*:初期先走纯Cypher直询路径。待图谱数据量和质量达到标准后，再开启Graphit进行叙事抽取和冲突消解功能。提供开关来控制Graphiti的启用。
9.*前端模块同步改造:涉及的前端模块也需要一并完成改造开发，与后端同步完成，并提供相应的前端改造方案。