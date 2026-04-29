const fs = require('fs')
const path = require('path')

// Read zh-CN.ts for mapping
const zhCnPath = path.join(__dirname, '../src/locales/zh-CN.ts')
const zhCnContent = fs.readFileSync(zhCnPath, 'utf-8')

const mapping = {}
const regex = /'([^']+)'\s*:\s*'([^']+)'/g
let m
while ((m = regex.exec(zhCnContent)) !== null) {
  const key = m[1]
  const value = m[2]
  if (!mapping[value]) mapping[value] = key
}

// Explicit mappings for phrases that may not be in zh-CN or need override
const explicit = {
  '市场': 'common.market',
  '品种': 'common.symbol',
  '分析类型': 'graphAnalysis.analysisType',
  '目标品种': 'graphAnalysis.targetSymbol',
  '事件UID': 'graphAnalysis.eventUid',
  '加密货币': 'market.crypto',
  '美股': 'market.stock',
  '港股': 'market.stock',
  'A股': 'market.stock',
  '股票': 'market.stock',
  '预测市场': 'market.crypto',
  '外汇': 'market.forex',
  '大宗商品': 'market.commodities',
  '行业板块': 'market.sectors',
  '图谱上下文': 'graphAnalysis.type.context',
  '传染路径': 'graphAnalysis.type.contagion',
  '聪明钱信号': 'graphAnalysis.type.smartMoney',
  '事件影响链': 'graphAnalysis.type.eventImpact',
  '查询图谱': 'graphAnalysis.query',
  '质量监控': 'graphAnalysis.qualityMonitor',
  '关系图谱': 'graphAnalysis.relationGraph',
  '当前品种:': 'graphAnalysis.currentSymbol',
  '图谱上下文分析': 'graphAnalysis.contextAnalysis',
  '图谱质量监控': 'graphAnalysis.qualityMonitorTitle',
  'Episode 数量': 'graphAnalysis.episodeCount',
  '实体数量': 'graphAnalysis.entityCount',
  '关系数量': 'graphAnalysis.relationCount',
  '阈值要求': 'graphAnalysis.thresholdHint',
  '关联资产': 'graphAnalysis.relatedAssets',
  '近期重大事件': 'graphAnalysis.recentEvents',
  '传染路径分析': 'graphAnalysis.contagionAnalysis',
  '路径': 'graphAnalysis.path',
  '深度': 'graphAnalysis.depth',
  '节点': 'graphAnalysis.node',
  '共识方向': 'graphAnalysis.consensus',
  '置信度分数': 'graphAnalysis.confidenceScore',
  '大户参与数': 'graphAnalysis.whaleCount',
  '事件影响链分析': 'graphAnalysis.eventImpactAnalysis',
  '影响半径': 'graphAnalysis.impactRadius',
  '最大分析深度': 'graphAnalysis.maxDepth',
  '受影响资产': 'graphAnalysis.affectedAssets',
  '受影响/关联事件': 'graphAnalysis.affectedEvents',
  '关联事件': 'graphAnalysis.relatedEvent',
  '恐惧贪婪指数': 'aiAnalysis.fearGreedIndex',
  '美元指数': 'aiAnalysis.dxy',
  '市场热力图': 'aiAnalysis.heatmap',
  '财经日历': 'aiAnalysis.economicCalendar',
  '暂无日历数据': 'aiAnalysis.noCalendarData',
  'AI 智能分析': 'aiAnalysis.title',
  '选择分析标的': 'aiAnalysis.selectSymbol',
  '输入标的代码': 'aiAnalysis.inputSymbol',
  '开始分析': 'aiAnalysis.startAnalysis',
  '分析结果': 'aiAnalysis.result',
  '历史记录': 'aiAnalysis.history',
  '输入标的并点击开始分析': 'aiAnalysis.emptyHint',
  '分析历史': 'aiAnalysis.analysisHistory',
  '查看': 'common.view',
  '确定删除？': 'common.confirmDelete',
  '关注列表': 'aiAnalysis.watchlist',
  '添加': 'common.add',
  '移除': 'common.remove',
  '持仓概览': 'portfolio.overview',
  '总仓位': 'portfolio.totalPositions',
  '总盈亏': 'portfolio.totalPnl',
  '监控任务': 'portfolio.monitorTasks',
  '暂无持仓': 'portfolio.noPositions',
  '添加关注': 'aiAnalysis.addWatchlist',
  '标的代码': 'aiAnalysis.symbolCode',
  '高影响': 'impact.high',
  '中影响': 'impact.medium',
  '低影响': 'impact.low',
  '已完成': 'status.completed',
  '分析中': 'status.processing',
  '失败': 'status.failed',
  '刷新价格': 'portfolio.refreshPrices',
  '新增资产': 'portfolio.addAsset',
  '资产分布': 'portfolio.assetDistribution',
  '系统设置': 'settings.title',
  '配置系统参数、API密钥和偏好设置': 'settings.subtitle',
  '需要重启服务才能生效': 'settings.restartRequired',
  '复制重启命令': 'settings.copyRestartCmd',
  '默认:': 'settings.defaultValue',
  '重置': 'common.reset',
  '保存': 'common.save',
  '加载设置失败': 'settings.loadFailed',
  '保存成功': 'common.saveSuccess',
  '保存失败': 'common.saveFailed',
  '已复制到剪贴板': 'common.copied',
  '所有状态': 'common.allStatus',
  '所有执行模式': 'common.allExecutionModes',
  '运行中': 'status.running',
  '已停止': 'status.stopped',
  '实盘': 'userManage.liveColon',
  '仅信号': 'userManage.signalColon',
  '启用': 'common.enable',
  '禁用': 'common.disable',
  '管理员': 'role.admin',
  '经理': 'role.manager',
  '用户': 'role.user',
  '编辑': 'common.edit',
  '积分': 'userManage.credits',
  '角色': 'common.role',
  'VIP': 'common.vip',
  '密码': 'common.password',
  '预警保存成功': 'common.saveSuccess',
  '监控任务已更新': 'common.updateSuccess',
  '监控已移除': 'common.deleted',
  '监控已启用': 'common.enable',
  '监控已禁用': 'common.disable',
  '监控任务运行中': 'common.loading',
  '任务已在后台启动，AI 分析结果将在完成后通过通知渠道推送。': 'common.info',
  '请选择指标': 'validation.indicatorRequired',
  '请输入策略名称': 'validation.strategyNameRequired',
  '请选择交易品种': 'validation.symbolRequired',
  '请输入初始资金': 'validation.initialCapitalRequired',
  '请输入杠杆': 'validation.leverageRequired',
  '地址': 'common.address',
  '名称': 'common.name',
  '胜率': 'common.winRate',
  '交易量': 'common.volume',
  '地址/账号': 'common.addressAccount',
  '余额': 'common.balance',
  '7日变动': 'common.change7d',
  '净值曲线': 'indicatorIde.equityCurve',
  '交易明细': 'indicatorIde.trades',
  'AI 参数优化': 'indicatorIde.aiOptimize',
  '总收益': 'indicatorIde.totalReturn',
  '最大回撤': 'indicatorIde.maxDrawdown',
  '夏普比率': 'indicatorIde.sharpeRatio',
  '交易次数': 'indicatorIde.tradeCount',
  'AI 实验': 'indicatorIde.aiExperimentTab',
  '回测运行中...': 'indicatorIde.runningBacktest',
  '配置参数后点击运行回测': 'indicatorIde.emptyHint',
  'AI 智能调优': 'indicatorIde.runAiExperiment',
  'AI 优化中': 'indicatorIde.aiOptimizing',
  '第': 'indicatorIde.round',
  '个候选': 'indicatorIde.candidates',
  '应用此参数': 'indicatorIde.applyThisCandidate',
  '回测此参数': 'indicatorIde.backtestThisCandidate',
  '参数变化': 'indicatorIde.tuningChangesTitle',
  '以下参数相比默认值有所变化': 'indicatorIde.tuningChangesHint',
  '参数已应用': 'indicatorIde.tuningChangesAlreadyApplied',
  '开发指南': 'indicatorIde.devGuide',
  '查看指标开发文档': 'indicatorIde.devGuideTooltip',
  '已购买指标': 'indicatorIde.purchasedIndicatorHintTitle',
  '已购买的指标为只读模式，可以使用但不能修改': 'indicatorIde.purchasedIndicatorHintDesc',
  '显示代码': 'indicatorIde.showCode',
  '隐藏代码': 'indicatorIde.hideCode',
  '显示快速交易': 'indicatorIde.showQuickTrade',
  '隐藏快速交易': 'indicatorIde.hideQuickTrade',
  '代码编辑器': 'indicatorIde.codeEditor',
  '未保存': 'indicatorIde.modified',
  '已购买': 'indicatorIde.purchasedReadOnlyTag',
  '已购': 'indicatorIde.purchasedBadge',
  '保存': 'indicatorIde.save',
  '已购买指标不可修改': 'indicatorIde.saveBlockedPurchased',
  '已购买指标不可删除': 'indicatorIde.deleteBlockedPurchased',
  '已购买指标不可发布': 'indicatorIde.publishBlockedPurchased',
  '另存为新指标': 'indicatorIde.saveAsNew',
  '在图表上运行': 'indicatorIde.runIndicatorOnChart',
  '停止图表运行': 'indicatorIde.stopIndicatorOnChart',
  '生成中...': 'indicatorIde.generating',
  'AI 生成代码': 'indicatorIde.aiGenerate',
  '描述你的指标逻辑，AI 将自动生成代码': 'indicatorIde.aiAssistHint',
  '例如：计算20日均线，当价格突破时发出信号...': 'indicatorIde.aiPromptPlaceholder',
  '生成代码': 'indicatorIde.generateCode',
  '去指标市场': 'indicatorIde.goIndicatorMarket',
  '代码质量': 'indicatorIde.codeQualityTitle',
  '重新检测': 'indicatorIde.codeQualityRecheck',
  'AI 质检': 'indicatorIde.aiQaTag',
  '已修复': 'indicatorIde.fixed',
  '待关注': 'indicatorIde.toWatch',
  '已自动修复': 'indicatorIde.autoFixed',
  '仍需关注': 'indicatorIde.needAttention',
  '回测参数': 'indicatorIde.backtestParameters',
  '历史记录': 'indicatorIde.history',
  '运行回测': 'indicatorIde.runBacktest',
  '时间范围': 'indicatorIde.dateRange',
  '开始': 'indicatorIde.start',
  '结束': 'indicatorIde.end',
  '资金设置': 'indicatorIde.capital',
  '初始资金': 'indicatorIde.initialCapital',
  '杠杆': 'indicatorIde.leverage',
  '手续费': 'indicatorIde.commission',
  '滑点': 'indicatorIde.slippage',
  '方向': 'indicatorIde.direction',
  '做多': 'indicatorIde.long',
  '做空': 'indicatorIde.short',
  '双向': 'indicatorIde.both',
  '高精度 MTF 模式': 'indicatorIde.highPrecisionMtf',
  '多时间框架高精度模式': 'indicatorIde.mtfHint',
  '从代码生成策略': 'indicatorIde.strategyFromCodeHint',
  '回测结果': 'indicatorIde.backtestResults',
  '运行中': 'status.running',
  '已停止': 'status.stopped',
  '异常': 'status.failed',
  '启动': 'common.start',
  '停止': 'common.stop',
  '网格交易': 'trading-bot.type.grid',
  '马丁格尔': 'trading-bot.type.martingale',
  '趋势跟随': 'trading-bot.type.trend',
  'DCA 定投': 'trading-bot.type.dca',
  '自定义脚本': 'trading-bot.type.custom',
  '基础配置': 'trading-bot.wizard.step1',
  '策略参数': 'trading-bot.wizard.step2',
  '风控设置': 'trading-bot.wizard.step3',
  '确认创建': 'trading-bot.wizard.step4',
  '上一步': 'trading-bot.wizard.prev',
  '下一步': 'trading-bot.wizard.next',
  '创建机器人': 'trading-bot.wizard.create',
  '机器人创建成功！': 'trading-bot.wizard.createSuccess',
  '数据源配置': 'dataSource.tabs.config',
  '数据集': 'dataSource.tabs.datasets',
  '同步任务': 'dataSource.tabs.sync',
  '添加数据源': 'dataSource.addConfig',
  '测试连接': 'dataSource.testConnection',
  '连接成功': 'dataSource.connected',
  '连接失败': 'dataSource.connectFail',
  '正常': 'dataSource.status.active',
  '禁用': 'dataSource.status.inactive',
  '立即同步': 'dataSource.sync.runNow',
  '同步中': 'dataSource.sync.status.running',
  '成功': 'dataSource.sync.status.success',
  '数据源管理': 'dataSource.title',
  'AI Keys': 'dataSource.tabs.keys',
  '返回首页': 'exception.backHome',
  '抱歉，您无权访问此页面': 'exception.403Desc',
  '抱歉，您访问的页面不存在': 'exception.404Desc',
  '抱歉，服务器出错了': 'exception.500Desc',
}

Object.assign(mapping, explicit)

const dirs = [
  path.join(__dirname, '../src/views'),
  path.join(__dirname, '../src/components'),
  path.join(__dirname, '../src/layouts'),
]

function getVueFiles(dir, files = []) {
  const items = fs.readdirSync(dir)
  for (const item of items) {
    const full = path.join(dir, item)
    const stat = fs.statSync(full)
    if (stat.isDirectory()) {
      getVueFiles(full, files)
    } else if (full.endsWith('.vue')) {
      files.push(full)
    }
  }
  return files
}

let totalFiles = 0
let modifiedFiles = 0

for (const dir of dirs) {
  if (!fs.existsSync(dir)) continue
  const files = getVueFiles(dir)
  for (const file of files) {
    totalFiles++
    let content = fs.readFileSync(file, 'utf-8')
    let original = content

    // Skip if no Chinese characters at all
    if (!/[\u4e00-\u9fa5]/.test(content)) continue

    // Replace attribute bindings that are not already bound
    // Use a function to avoid replacing already-bound attributes
    function replaceAttr(attr, text, replacement) {
      const pattern = new RegExp(`\\b${attr}="${text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`, 'g')
      content = content.replace(pattern, replacement)
    }

    // Batch replace common attributes
    for (const [text, key] of Object.entries(mapping)) {
      if (!text || !key) continue
      const escaped = text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      // label
      content = content.replace(new RegExp(`label="${escaped}"`, 'g'), `:label="t('${key}')"`)
      // tab
      content = content.replace(new RegExp(`tab="${escaped}"`, 'g'), `:tab="t('${key}')"`)
      // title (but not already :title)
      content = content.replace(new RegExp(`(?<!:)title="${escaped}"`, 'g'), `:title="t('${key}')"`)
      // description
      content = content.replace(new RegExp(`description="${escaped}"`, 'g'), `:description="t('${key}')"`)
      // message
      content = content.replace(new RegExp(`message="${escaped}"`, 'g'), `:message="t('${key}')"`)
      // placeholder
      content = content.replace(new RegExp(`placeholder="${escaped}"`, 'g'), `:placeholder="t('${key}')"`)
      // empty-text
      content = content.replace(new RegExp(`empty-text="${escaped}"`, 'g'), `:empty-text="t('${key}')"`)
      // a-statistic title
      content = content.replace(new RegExp(`<a-statistic title="${escaped}"`, 'g'), `<a-statistic :title="t('${key}')"`)
      // a-descriptions-item label
      content = content.replace(new RegExp(`<a-descriptions-item label="${escaped}"`, 'g'), `<a-descriptions-item :label="t('${key}')"`)
    }

    // Replace button/tag text patterns
    // Match <a-button ...>text</a-button> where text is pure Chinese
    content = content.replace(/(<a-button[^>]*)>([\u4e00-\u9fa5\s]+)<\/a-button>/g, (match, open, text) => {
      const key = mapping[text.trim()]
      if (key) return `${open}>{{ t('${key}') }}</a-button>`
      return match
    })

    // Match <a-tag ...>text</a-tag>
    content = content.replace(/(<a-tag[^>]*)>([\u4e00-\u9fa5\s:]+)<\/a-tag>/g, (match, open, text) => {
      const key = mapping[text.trim()]
      if (key) return `${open}>{{ t('${key}') }}</a-tag>`
      return match
    })

    // Match <span>text</span> for common labels
    content = content.replace(/(<span[^>]*)>([\u4e00-\u9fa5\s]+)<\/span>/g, (match, open, text) => {
      const key = mapping[text.trim()]
      if (key && !open.includes('v-if') && !open.includes('v-show')) return `<span>{{ t('${key}') }}</span>`
      return match
    })

    // Replace a-empty description
    content = content.replace(/<a-empty\s+description="([^"]+)"\s*\/>/g, (match, text) => {
      const key = mapping[text]
      if (key) return `<a-empty :description="t('${key}')" />`
      return match
    })

    // Replace table column titles in script
    content = content.replace(/title:\s*'([^']+)'/g, (match, text) => {
      const key = mapping[text]
      if (key) return `title: t('${key}')`
      return match
    })

    // Replace remaining message patterns
    content = content.replace(/message\.success\('([^']+)'\)/g, (match, text) => {
      const key = mapping[text]
      if (key) return `message.success(t('${key}'))`
      return match
    })
    content = content.replace(/message\.error\('([^']+)'\)/g, (match, text) => {
      const key = mapping[text]
      if (key) return `message.error(t('${key}'))`
      return match
    })
    content = content.replace(/message\.warning\('([^']+)'\)/g, (match, text) => {
      const key = mapping[text]
      if (key) return `message.warning(t('${key}'))`
      return match
    })

    if (content !== original) {
      fs.writeFileSync(file, content, 'utf-8')
      modifiedFiles++
      console.log('Modified:', path.relative(path.join(__dirname, '..'), file))
    }
  }
}

console.log(`\nTotal files scanned: ${totalFiles}`)
console.log(`Files modified: ${modifiedFiles}`)
