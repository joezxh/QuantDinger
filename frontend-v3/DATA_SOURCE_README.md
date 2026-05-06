# 📊 数据源管理前端界面

> QuantDinger 数据源全生命周期管理平台

[![Vue 3](https://img.shields.io/badge/Vue-3.4+-brightgreen.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![Ant Design Vue](https://img.shields.io/badge/Ant%20Design%20Vue-4.1+-2a58d8.svg)](https://antdv.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 项目简介

基于 QuantDinger 后端的数据源配置管理功能，开发的一套完整的前端管理界面，提供：

- ✅ **数据源配置管理** - 全生命周期CRUD操作
- ✅ **API密钥管理** - 多密钥负载均衡与健康监控
- ✅ **限流配置管理** - 灵活策略与实时统计
- ✅ **健康状态监控** - 全局监控与性能分析

## 🚀 快速开始

### 安装依赖

```bash
cd frontend-v3
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:5173/data-source

### 构建生产版本

```bash
npm run build
```

## 📁 目录结构

```
frontend-v3/src/views/data-source/
├── index.vue                    # 📋 主页面（标签页布局）
├── components/
│   ├── ConfigList.vue          # ⚙️ 数据源配置列表（增强版）
│   ├── KeyList.vue             # 🔑 API密钥列表（旧版）
│   ├── DatasetList.vue         # 📊 数据集列表
│   └── SyncTaskTab.vue         # 🔄 同步任务
├── ApiKeyManager.vue           # 🔐 API密钥管理（新版）
├── RateLimitManager.vue        # ⚡ 限流配置管理
└── HealthDashboard.vue         # 💚 健康状态监控

frontend-v3/src/api/
└── data-source.ts              # 🌐 API接口封装（29个函数）
```

## 🎨 功能特性

### 1. 数据源配置管理

| 功能 | 状态 | 说明 |
|------|------|------|
| 列表展示 | ✅ | 表格视图，支持分页 |
| 搜索过滤 | ✅ | 按名称、代码、层、类别 |
| 新增配置 | ✅ | 完整的表单验证 |
| 编辑配置 | ✅ | 实时更新 |
| 删除配置 | ✅ | 二次确认 |
| 启用/禁用 | ✅ | 开关控制，即时生效 |
| 健康检查 | ✅ | 快速测试连接 |
| 快捷跳转 | ✅ | 密钥/限流管理入口 |

**访问路径**: `/data-source`

---

### 2. API密钥管理

| 功能 | 状态 | 说明 |
|------|------|------|
| 密钥列表 | ✅ | 显示所有密钥 |
| 添加密钥 | ✅ | 加密存储 |
| 编辑密钥 | ✅ | 安全更新 |
| 删除密钥 | ✅ | 安全删除 |
| 启用/禁用 | ✅ | 状态切换 |
| 使用统计 | ✅ | 今日调用次数 |
| 进度条 | ✅ | 颜色编码使用率 |
| 健康监控 | ✅ | 连续错误追踪 |
| 权重配置 | ✅ | 负载均衡支持 |

**访问路径**: `/data-source/keys?source_code=crypto_ccxt`

---

### 3. 限流配置管理

| 功能 | 状态 | 说明 |
|------|------|------|
| 策略选择 | ✅ | 4种限流策略 |
| 参数配置 | ✅ | 速率/周期/突发/并发 |
| 自适应限流 | ✅ | 动态调整 |
| 错误降速 | ✅ | 保护机制 |
| 统计展示 | ✅ | 实时数据 |
| 状态监控 | ✅ | 当前速率/令牌/并发 |

**访问路径**: `/data-source/rate-limit?source_code=crypto_ccxt`

**支持的限流策略**:
- 🔵 **令牌桶** (Token Bucket) - 允许突发流量
- 🟢 **滑动窗口** (Sliding Window) - 精确控制
- 🟡 **固定窗口** (Fixed Window) - 简单限流
- 🟣 **自适应** (Adaptive) - 智能调整

---

### 4. 健康状态监控

| 功能 | 状态 | 说明 |
|------|------|------|
| 全局概览 | ✅ | 4个统计卡片 |
| 全面检查 | ✅ | 并行检查所有数据源 |
| 单独检查 | ✅ | 快速定位问题 |
| 状态显示 | ✅ | 颜色编码 |
| 响应时间 | ✅ | 性能指标 |
| 错误信息 | ✅ | 详细错误 |
| 详情查看 | ✅ | 完整配置信息 |

**访问路径**: `/data-source/health`

**响应时间颜色编码**:
- 🟢 绿色: < 200ms (优秀)
- 🟠 橙色: 200-500ms (一般)
- 🔴 红色: > 500ms (较差)

---

## 📖 文档

| 文档 | 说明 | 链接 |
|------|------|------|
| 📘 快速启动指南 | 5分钟上手教程 | [QUICK_START.md](QUICK_START.md) |
| 📗 完整使用手册 | 详细功能说明 | [DATA_SOURCE_MANAGER_GUIDE.md](DATA_SOURCE_MANAGER_GUIDE.md) |
| 📙 开发总结 | 技术架构与实现 | [DATA_SOURCE_MANAGEMENT_SUMMARY.md](DATA_SOURCE_MANAGEMENT_SUMMARY.md) |

---

## 🛠️ 技术栈

### 前端技术

- **框架**: Vue 3.4+ (Composition API)
- **语言**: TypeScript 5.3+
- **UI库**: Ant Design Vue 4.1+
- **路由**: Vue Router 4.2+
- **HTTP**: Axios
- **构建**: Vite 5.0+

### 后端依赖

- **框架**: Flask (Python)
- **数据库**: PostgreSQL 16
- **ORM**: SQLAlchemy
- **加密**: AES-256-GCM
- **限流**: Token Bucket Algorithm

---

## 🔌 API接口

### 数据源配置 (7个接口)

```typescript
GET    /api/data-sources/                      # 获取列表
GET    /api/data-sources/{code}                # 获取详情
POST   /api/data-sources/                      # 创建
PUT    /api/data-sources/{code}                # 更新
DELETE /api/data-sources/{code}                # 删除
POST   /api/data-sources/{code}/toggle         # 启用/禁用
POST   /api/data-sources/health/{code}         # 健康检查
```

### API密钥 (5个接口)

```typescript
GET    /api/data-sources/{code}/api-keys       # 获取密钥列表
POST   /api/data-sources/{code}/api-keys       # 添加密钥
PUT    /api/data-sources/{code}/api-keys/{id}  # 更新密钥
DELETE /api/data-sources/{code}/api-keys/{id}  # 删除密钥
POST   /api/data-sources/{code}/api-keys/{id}/toggle  # 启用/禁用
```

### 限流配置 (3个接口)

```typescript
GET    /api/data-sources/{code}/rate-limit     # 获取配置
PUT    /api/data-sources/{code}/rate-limit     # 更新配置
GET    /api/data-sources/{code}/rate-limit/stats  # 获取统计
```

### 其他接口 (14个)

健康状态、优先级调整、宏观经济、新闻、DeFi、CFTC、CBOE、BEA、基本面等

**总计**: 29个API接口函数

---

## 🎯 使用场景

### 场景1: 新增数据源

```
1. 访问 /data-source
2. 点击"新增数据源"
3. 填写配置表单
4. 保存成功
```

### 场景2: 配置API密钥

```
1. 在数据源列表点击"密钥管理"
2. 点击"添加密钥"
3. 填写密钥信息
4. 设置权重和限制
5. 保存成功
```

### 场景3: 设置限流规则

```
1. 在数据源列表点击"限流配置"
2. 选择限流策略
3. 配置参数
4. 启用自适应
5. 保存配置
```

### 场景4: 监控健康状态

```
1. 访问 /data-source/health
2. 点击"全面健康检查"
3. 查看所有数据源状态
4. 处理异常数据源
```

---

## 📊 界面预览

### 数据源配置列表
- 表格展示所有数据源
- 实时健康状态
- API密钥配置情况
- 限流策略信息
- 快捷操作入口

### API密钥管理
- 密钥列表展示
- 使用进度条
- 健康状态监控
- 权重配置
- 快捷操作

### 限流配置
- 双栏布局
- 配置表单
- 实时统计
- 状态监控

### 健康监控
- 全局统计卡片
- 健康状态列表
- 响应时间颜色编码
- 详情对话框

---

## 🔐 安全特性

- ✅ API密钥加密存储（AES-256-GCM）
- ✅ 管理员权限验证
- ✅ CSRF保护
- ✅ 请求频率限制
- ✅ 输入数据验证
- ✅ 错误信息脱敏

---

## 🎨 设计特点

### 用户体验
- 🎯 直观的操作流程
- 💬 完整的操作反馈
- ⚡ 快速的响应速度
- 📱 响应式设计
- ♿ 无障碍访问支持

### 视觉设计
- 🎨 统一的配色方案
- 🌈 状态颜色编码
- 📐 规范的间距布局
- 🔤 清晰的字体层级
- 💫 优雅的过渡动画

---

## 📈 性能优化

- ⚡ 路由懒加载
- 🔄 按需加载组件
- 📦 代码分割
- 🚀 并行请求优化
- 💾 浏览器缓存
- 📉 分页显示

---

## 🧪 测试建议

### 功能测试
- [ ] 数据源CRUD操作
- [ ] API密钥管理
- [ ] 限流配置
- [ ] 健康检查
- [ ] 搜索过滤
- [ ] 表单验证

### 集成测试
- [ ] API接口联调
- [ ] 路由跳转
- [ ] 权限控制
- [ ] 错误处理

### 性能测试
- [ ] 页面加载速度
- [ ] 接口响应时间
- [ ] 大数据量渲染
- [ ] 并发请求处理

---

## 🚧 后续计划

### v1.1.0 (短期)
- [ ] 配置导入/导出
- [ ] 批量操作
- [ ] 配置模板
- [ ] 移动端优化

### v1.2.0 (中期)
- [ ] 实时监控告警
- [ ] 使用趋势图表
- [ ] 配置历史记录
- [ ] WebSocket推送

### v2.0.0 (长期)
- [ ] AI智能优化
- [ ] 自动故障修复
- [ ] 第三方监控集成
- [ ] 配置审计系统

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范
- 使用 ESLint + Prettier
- 遵循 Vue Style Guide
- 完整的 TypeScript 类型定义
- 组件命名使用 PascalCase
- 文件命名使用 kebab-case

---

## 📝 更新日志

### v1.0.0 (2026-05-03)
- ✅ 数据源配置管理
- ✅ API密钥管理
- ✅ 限流配置管理
- ✅ 健康状态监控
- ✅ 29个API接口
- ✅ 完整文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 👥 团队

- **开发**: AI Assistant
- **设计**: Ant Design Vue
- **测试**: Community

---

## 📞 联系方式

- 📧 Email: support@quantdinger.com
- 💬 Discord: [加入社区](#)
- 🐛 Issue: [提交问题](#)
- 📖 文档: [查看文档](#)

---

## 🙏 致谢

感谢以下开源项目：

- [Vue.js](https://vuejs.org/)
- [Ant Design Vue](https://antdv.com/)
- [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/)

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**

[返回顶部](#-数据源管理前端界面)
