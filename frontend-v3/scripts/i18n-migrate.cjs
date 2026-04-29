const fs = require('fs')
const path = require('path')

// Build reverse mapping from zh-CN.ts
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

// Additional explicit mappings for common phrases
const explicitMapping = {
  '账单管理': 'billing.title',
  '管理您的积分、VIP会员和套餐': 'billing.subtitle',
  '当前积分': 'billing.currentCredits',
  'VIP状态': 'billing.vipStatus',
  '非VIP': 'billing.notVip',
  'VIP会员规则': 'billing.vipRules',
  'VIP会员每月获得额外积分奖励，可在有效期内享受高级功能。': 'billing.vipRulesDesc',
  '月度套餐': 'billing.planMonthly',
  '年度套餐': 'billing.planYearly',
  '永久会员': 'billing.planLifetime',
  '立即购买': 'billing.buyNow',
  'USDT 支付': 'billing.usdtPayTitle',
  '请扫描下方二维码完成支付': 'billing.usdtPayDesc',
  '收款地址': 'billing.receiverAddress',
  '复制地址': 'billing.copyAddress',
  '支付金额': 'billing.payAmount',
  '复制金额': 'billing.copyAmount',
  '请使用TRC20网络转账，确认后将自动到账': 'billing.trc20Warning',
  '订单已过期': 'billing.orderExpired',
  '支付成功': 'billing.paySuccess',
  '刷新状态': 'billing.refreshStatus',
  '完成': 'billing.done',
  '加载失败': 'common.loadFailed',
  '购买失败': 'common.purchaseFailed',
  '复制成功': 'common.copySuccess',
  '复制失败': 'common.copyFailed',
  '系统管理 & 用户运营': 'userManage.title',
  '全平台用户生命周期管理、策略运行监控及业务运营看板': 'userManage.subtitle',
  '用户管理': 'userManage.tab.users',
  '系统实盘概览': 'userManage.tab.strategies',
  '充值订单管理': 'userManage.tab.orders',
  'AI分析运营': 'userManage.tab.aiStats',
  '总用户数': 'userManage.totalUsers',
  '今日新增': 'userManage.todayNew',
  '活跃VIP': 'userManage.activeVips',
  '全平台积分': 'userManage.totalCredits',
  '创建用户': 'userManage.createUser',
  '导出用户': 'userManage.exportUsers',
  '搜索用户名/邮箱/昵称': 'userManage.searchPlaceholder',
  '从未登录': 'userManage.neverLogin',
  '总策略数': 'userManage.totalStrategies',
  '总保证金 (USDT)': 'userManage.totalCapital',
  '实盘托管': 'userManage.executionLive',
  '仅信号通知': 'userManage.executionSignal',
  '搜索策略/品种/用户': 'userManage.strategySearchPlaceholder',
  '当前权益': 'userManage.currentEquity',
  '盈亏 (USDT)': 'userManage.pnlUsdt',
  '总订单数': 'userManage.totalOrders',
  '总收入': 'userManage.totalRevenue',
  '充值地址': 'userManage.rechargeAddress',
  '交易哈希': 'userManage.txHash',
  '总分析次数': 'userManage.totalAnalyses',
  '活跃分析用户': 'userManage.activeAnalysisUsers',
  '覆盖代币数': 'userManage.coveredSymbols',
  'AI准确率 (验证通过/总记忆)': 'userManage.aiAccuracy',
  '用户分析排行': 'userManage.userAnalysisRanking',
  '分析次数': 'userManage.analysisCount',
  '准确率 (对/错)': 'userManage.accuracy',
  '反馈 (赞/踩)': 'userManage.feedback',
  '最后分析时间': 'userManage.lastAnalysisTime',
  '最近分析记录': 'userManage.recentAnalysisRecords',
  '编辑用户': 'userManage.editUser',
  '创建用户': 'userManage.createUser',
  '重置密码': 'userManage.resetPassword',
  '此操作将重置用户密码': 'userManage.resetPasswordWarning',
  '调整积分': 'userManage.adjustCredits',
  '当前积分:': 'userManage.currentCredits',
  '新积分': 'userManage.newCredits',
  '设置VIP': 'userManage.setVip',
  'VIP天数': 'userManage.vipDays',
  '取消VIP': 'userManage.cancelVip',
  '到期时间': 'userManage.expiryTime',
  '分配角色': 'userManage.assignRole',
  '策略概览加载失败': 'userManage.strategyLoadFailed',
  '订单加载失败': 'userManage.orderLoadFailed',
  'AI统计加载失败': 'userManage.aiStatsLoadFailed',
  '更新成功': 'common.updateSuccess',
  '创建成功': 'common.createSuccess',
  '已删除': 'common.deleted',
  '删除失败': 'common.deleteFailed',
  '密码已重置': 'userManage.passwordResetSuccess',
  '重置失败': 'userManage.resetFailed',
  '积分已更新': 'userManage.creditsUpdated',
  '更新失败': 'common.updateFailed',
  'VIP设置成功': 'userManage.vipSetSuccess',
  '请选择日期': 'common.pleaseSelectDate',
  '角色分配成功': 'userManage.roleAssigned',
  '加载角色数据失败': 'userManage.roleLoadFailed',
  '导出成功': 'common.exportSuccess',
  '导出失败': 'common.exportFailed',
  '知识图谱分析': 'graphAnalysis.title',
  '基于图谱的跨域关联推理与事件影响分析': 'graphAnalysis.subtitle',
  '查询图谱': 'graphAnalysis.query',
  '质量监控': 'graphAnalysis.qualityMonitor',
  '关系图谱': 'graphAnalysis.relationGraph',
  '图谱上下文分析': 'graphAnalysis.contextAnalysis',
  '请输入市场与品种后查询': 'graphAnalysis.contextEmpty',
  '图谱质量监控': 'graphAnalysis.qualityMonitorTitle',
  'Episode 数量': 'graphAnalysis.episodeCount',
  '实体数量': 'graphAnalysis.entityCount',
  '关系数量': 'graphAnalysis.relationCount',
  '数据质量达标': 'graphAnalysis.qualityReady',
  '数据积累中': 'graphAnalysis.qualityBuilding',
  '阈值要求': 'graphAnalysis.thresholdHint',
  '点击质量监控按钮查看': 'graphAnalysis.qualityEmpty',
  '关联资产': 'graphAnalysis.relatedAssets',
  '近期重大事件': 'graphAnalysis.recentEvents',
  '传染路径分析': 'graphAnalysis.contagionAnalysis',
  '风险评估得分:': 'graphAnalysis.riskScore',
  '发现路径数:': 'graphAnalysis.pathCount',
  '未找到传播路径': 'graphAnalysis.noContagionPath',
  '请选择两个品种后查询传染路径': 'graphAnalysis.contagionHint',
  '聪明钱 (Smart Money) 信号': 'graphAnalysis.smartMoneyTitle',
  '共识方向': 'graphAnalysis.consensus',
  '置信度分数': 'graphAnalysis.confidenceScore',
  '大户参与数': 'graphAnalysis.whaleCount',
  '请选择品种后查询聪明钱信号': 'graphAnalysis.smartMoneyHint',
  '事件影响链分析': 'graphAnalysis.eventImpactAnalysis',
  '事件 UID': 'graphAnalysis.eventUidLabel',
  '影响半径': 'graphAnalysis.impactRadius',
  '最大分析深度': 'graphAnalysis.maxDepth',
  '受影响资产': 'graphAnalysis.affectedAssets',
  '受影响/关联事件': 'graphAnalysis.affectedEvents',
  '关联事件': 'graphAnalysis.relatedEvent',
  '请输入事件 UID 后查询影响链': 'graphAnalysis.eventImpactHint',
  '请输入品种代码': 'validation.symbolRequired',
  '查询上下文失败': 'graphAnalysis.contextQueryFailed',
  '图谱查询失败': 'graphAnalysis.graphQueryFailed',
  '质量监控加载失败': 'graphAnalysis.qualityLoadFailed',
  '请输入目标品种': 'validation.targetSymbolRequired',
  '传染路径查询失败': 'graphAnalysis.contagionQueryFailed',
  '聪明钱信号查询失败': 'graphAnalysis.smartMoneyQueryFailed',
  '请输入事件 UID': 'validation.eventUidRequired',
  '事件影响链查询失败': 'graphAnalysis.eventImpactQueryFailed',
  '我的投资组合': 'portfolio.myPortfolio',
  '实时追踪资产变动，AI 驱动的风险评估与多维度监控': 'portfolio.subtitle',
  '刷新价格': 'portfolio.refreshPrices',
  '新增资产': 'portfolio.addAsset',
  '资产分布': 'portfolio.assetDistribution',
  '系统设置': 'settings.title',
  '配置系统参数、API密钥和偏好设置': 'settings.subtitle',
  '需要重启服务才能生效': 'settings.restartRequired',
  '复制重启命令': 'settings.copyRestartCmd',
  '请输入': 'common.pleaseInput',
  '请输入密钥': 'common.pleaseInputKey',
  '请选择': 'common.pleaseSelect',
  '默认:': 'settings.defaultValue',
  '重置': 'common.reset',
  '保存': 'common.save',
  '加载设置失败': 'settings.loadFailed',
  '保存成功': 'common.saveSuccess',
  '保存失败': 'common.saveFailed',
  '已复制到剪贴板': 'common.copied',
  'AI driven quantitative insights for global markets': '',
  'Username': 'user.login.username',
  'Password': 'user.login.password',
  'Please enter username': 'user.login.usernameRequired',
  'Please enter password': 'user.login.passwordRequired',
  'Login': 'user.login.submit',
  'Login successful': 'user.login.success',
  'Login failed': 'user.login.failed',
  "Don't have an account? Register": 'user.login.registerHint',
}

Object.assign(mapping, explicitMapping)

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
    const hasI18nImport = content.includes('useI18n')
    const isSetup = content.includes('<script setup')

    if (!hasI18nImport && isSetup) {
      // Add import
      const importMatch = content.match(/import\s+\{[^}]+\}\s+from\s+'vue'/)
      if (importMatch) {
        const end = importMatch.index + importMatch[0].length
        content = content.slice(0, end) + "\nimport { useI18n } from 'vue-i18n'" + content.slice(end)
      } else {
        const scriptMatch = content.match(/<script setup lang="ts">/)
        if (scriptMatch) {
          const end = scriptMatch.index + scriptMatch[0].length
          content = content.slice(0, end) + "\nimport { useI18n } from 'vue-i18n'" + content.slice(end)
        }
      }

      // Add const { t } = useI18n()
      const scriptStart = content.match(/<script setup lang="ts">/)
      if (scriptStart) {
        const afterScript = content.slice(scriptStart.index + scriptStart[0].length)
        const firstConst = afterScript.match(/\nconst\s+\w+\s+=/)
        if (firstConst) {
          const pos = scriptStart.index + scriptStart[0].length + firstConst.index
          content = content.slice(0, pos) + "\nconst { t } = useI18n()" + content.slice(pos)
        }
      }
    }

    // Replace common message patterns
    content = content.replace(/message\.success\('([^']+)'\)/g, (match, p1) => {
      const key = mapping[p1]
      if (key) return `message.success(t('${key}'))`
      return match
    })
    content = content.replace(/message\.error\('([^']+)'\)/g, (match, p1) => {
      const key = mapping[p1]
      if (key) return `message.error(t('${key}'))`
      return match
    })
    content = content.replace(/message\.warning\('([^']+)'\)/g, (match, p1) => {
      const key = mapping[p1]
      if (key) return `message.warning(t('${key}'))`
      return match
    })

    // Replace template text patterns (simple >text< without attributes)
    // Only replace known short phrases to avoid breaking things
    const safeReplacements = [
      ['>账单管理<', '>{{ t(\'billing.title\') }}<'],
      ['>管理您的积分、VIP会员和套餐<', '>{{ t(\'billing.subtitle\') }}<'],
      ['>当前积分<', '>{{ t(\'billing.currentCredits\') }}<'],
      ['>VIP状态<', '>{{ t(\'billing.vipStatus\') }}<'],
      ['>非VIP<', '>{{ t(\'billing.notVip\') }}<'],
      ['>VIP会员规则<', '>:message="t(\'billing.vipRules\')"'],
      ['>月度套餐<', '>{{ t(\'billing.planMonthly\') }}<'],
      ['>年度套餐<', '>{{ t(\'billing.planYearly\') }}<'],
      ['>永久会员<', '>{{ t(\'billing.planLifetime\') }}<'],
      ['>立即购买<', '>{{ t(\'billing.buyNow\') }}<'],
      ['>USDT 支付<', '>{{ t(\'billing.usdtPayTitle\') }}<'],
      ['>请扫描下方二维码完成支付<', '>{{ t(\'billing.usdtPayDesc\') }}<'],
      ['>收款地址<', '>{{ t(\'billing.receiverAddress\') }}<'],
      ['>支付金额<', '>{{ t(\'billing.payAmount\') }}<'],
      ['>请使用TRC20网络转账，确认后将自动到账<', '>{{ t(\'billing.trc20Warning\') }}<'],
      ['>刷新状态<', '>{{ t(\'billing.refreshStatus\') }}<'],
      ['>完成<', '>{{ t(\'billing.done\') }}<'],
      ['>关闭<', '>{{ t(\'common.close\') }}<'],
      ['>系统管理 & 用户运营<', '>{{ t(\'userManage.title\') }}<'],
      ['>全平台用户生命周期管理、策略运行监控及业务运营看板<', '>{{ t(\'userManage.subtitle\') }}<'],
      ['>用户管理<', '>{{ t(\'userManage.tab.users\') }}<'],
      ['>系统实盘概览<', '>{{ t(\'userManage.tab.strategies\') }}<'],
      ['>充值订单管理<', '>{{ t(\'userManage.tab.orders\') }}<'],
      ['>AI分析运营<', '>{{ t(\'userManage.tab.aiStats\') }}<'],
      ['>总用户数<', '>{{ t(\'userManage.totalUsers\') }}<'],
      ['>今日新增<', '>{{ t(\'userManage.todayNew\') }}<'],
      ['>活跃VIP<', '>{{ t(\'userManage.activeVips\') }}<'],
      ['>全平台积分<', '>{{ t(\'userManage.totalCredits\') }}<'],
      ['>创建用户<', '>{{ t(\'userManage.createUser\') }}<'],
      ['>导出用户<', '>{{ t(\'userManage.exportUsers\') }}<'],
      ['>从未登录<', '>{{ t(\'userManage.neverLogin\') }}<'],
      ['>总策略数<', '>{{ t(\'userManage.totalStrategies\') }}<'],
      ['>总保证金 (USDT)<', '>{{ t(\'userManage.totalCapital\') }}<'],
      ['>实盘托管<', '>{{ t(\'userManage.executionLive\') }}<'],
      ['>仅信号通知<', '>{{ t(\'userManage.executionSignal\') }}<'],
      ['>当前权益<', '>{{ t(\'userManage.currentEquity\') }}<'],
      ['>盈亏 (USDT)<', '>{{ t(\'userManage.pnlUsdt\') }}<'],
      ['>总订单数<', '>{{ t(\'userManage.totalOrders\') }}<'],
      ['>总收入<', '>{{ t(\'userManage.totalRevenue\') }}<'],
      ['>充值地址<', '>{{ t(\'userManage.rechargeAddress\') }}<'],
      ['>交易哈希<', '>{{ t(\'userManage.txHash\') }}<'],
      ['>总分析次数<', '>{{ t(\'userManage.totalAnalyses\') }}<'],
      ['>活跃分析用户<', '>{{ t(\'userManage.activeAnalysisUsers\') }}<'],
      ['>覆盖代币数<', '>{{ t(\'userManage.coveredSymbols\') }}<'],
      ['>AI准确率 (验证通过/总记忆)<', '>{{ t(\'userManage.aiAccuracy\') }}<'],
      ['>用户分析排行<', '>{{ t(\'userManage.userAnalysisRanking\') }}<'],
      ['>分析次数<', '>{{ t(\'userManage.analysisCount\') }}<'],
      ['>准确率 (对/错)<', '>{{ t(\'userManage.accuracy\') }}<'],
      ['>反馈 (赞/踩)<', '>{{ t(\'userManage.feedback\') }}<'],
      ['>最后分析时间<', '>{{ t(\'userManage.lastAnalysisTime\') }}<'],
      ['>最近分析记录<', '>{{ t(\'userManage.recentAnalysisRecords\') }}<'],
      ['>编辑用户<', '>{{ t(\'userManage.editUser\') }}<'],
      ['>重置密码<', '>{{ t(\'userManage.resetPassword\') }}<'],
      ['>此操作将重置用户密码<', '>:message="t(\'userManage.resetPasswordWarning\')"'],
      ['>调整积分<', '>{{ t(\'userManage.adjustCredits\') }}<'],
      ['>当前积分:<', '>{{ t(\'userManage.currentCredits\') }}<'],
      ['>新积分<', '>{{ t(\'userManage.newCredits\') }}<'],
      ['>设置VIP<', '>{{ t(\'userManage.setVip\') }}<'],
      ['>VIP天数<', '>{{ t(\'userManage.vipDays\') }}<'],
      ['>取消VIP<', '>{{ t(\'userManage.cancelVip\') }}<'],
      ['>到期时间<', '>{{ t(\'userManage.expiryTime\') }}<'],
      ['>分配角色<', '>{{ t(\'userManage.assignRole\') }}<'],
      ['>知识图谱分析<', '>{{ t(\'graphAnalysis.title\') }}<'],
      ['>基于图谱的跨域关联推理与事件影响分析<', '>{{ t(\'graphAnalysis.subtitle\') }}<'],
      ['>查询图谱<', '>{{ t(\'graphAnalysis.query\') }}<'],
      ['>质量监控<', '>{{ t(\'graphAnalysis.qualityMonitor\') }}<'],
      ['>关系图谱<', '>{{ t(\'graphAnalysis.relationGraph\') }}<'],
      ['>图谱上下文分析<', '>{{ t(\'graphAnalysis.contextAnalysis\') }}<'],
      ['>请输入市场与品种后查询<', '>:empty-text="t(\'graphAnalysis.contextEmpty\')"'],
      ['>图谱质量监控<', '>{{ t(\'graphAnalysis.qualityMonitorTitle\') }}<'],
      ['>Episode 数量<', '>{{ t(\'graphAnalysis.episodeCount\') }}<'],
      ['>实体数量<', '>{{ t(\'graphAnalysis.entityCount\') }}<'],
      ['>关系数量<', '>{{ t(\'graphAnalysis.relationCount\') }}<'],
      ['>数据质量达标<', '>:message="t(\'graphAnalysis.qualityReady\')"'],
      ['>数据积累中<', '>:message="t(\'graphAnalysis.qualityBuilding\')"'],
      ['>阈值要求<', '>{{ t(\'graphAnalysis.thresholdHint\') }}<'],
      ['>点击质量监控按钮查看<', '>:description="t(\'graphAnalysis.qualityEmpty\')"'],
      ['>关联资产<', '>{{ t(\'graphAnalysis.relatedAssets\') }}<'],
      ['>近期重大事件<', '>{{ t(\'graphAnalysis.recentEvents\') }}<'],
      ['>传染路径分析<', '>{{ t(\'graphAnalysis.contagionAnalysis\') }}<'],
      ['>风险评估得分:<', '>{{ t(\'graphAnalysis.riskScore\') }}<'],
      ['>发现路径数:<', '>{{ t(\'graphAnalysis.pathCount\') }}<'],
      ['>未找到传播路径<', '>:description="t(\'graphAnalysis.noContagionPath\')"'],
      ['>请选择两个品种后查询传染路径<', '>:description="t(\'graphAnalysis.contagionHint\')"'],
      ['>聪明钱 (Smart Money) 信号<', '>{{ t(\'graphAnalysis.smartMoneyTitle\') }}<'],
      ['>共识方向<', '>{{ t(\'graphAnalysis.consensus\') }}<'],
      ['>置信度分数<', '>{{ t(\'graphAnalysis.confidenceScore\') }}<'],
      ['>大户参与数<', '>{{ t(\'graphAnalysis.whaleCount\') }}<'],
      ['>请选择品种后查询聪明钱信号<', '>:description="t(\'graphAnalysis.smartMoneyHint\')"'],
      ['>事件影响链分析<', '>{{ t(\'graphAnalysis.eventImpactAnalysis\') }}<'],
      ['>事件 UID<', '>{{ t(\'graphAnalysis.eventUidLabel\') }}<'],
      ['>影响半径<', '>{{ t(\'graphAnalysis.impactRadius\') }}<'],
      ['>最大分析深度<', '>{{ t(\'graphAnalysis.maxDepth\') }}<'],
      ['>受影响资产<', '>{{ t(\'graphAnalysis.affectedAssets\') }}<'],
      ['>受影响/关联事件<', '>{{ t(\'graphAnalysis.affectedEvents\') }}<'],
      ['>关联事件<', '>{{ t(\'graphAnalysis.relatedEvent\') }}<'],
      ['>请输入事件 UID 后查询影响链<', '>:description="t(\'graphAnalysis.eventImpactHint\')"'],
      ['>我的投资组合<', '>{{ t(\'portfolio.myPortfolio\') }}<'],
      ['>实时追踪资产变动，AI 驱动的风险评估与多维度监控<', '>{{ t(\'portfolio.subtitle\') }}<'],
      ['>刷新价格<', '>{{ t(\'portfolio.refreshPrices\') }}<'],
      ['>新增资产<', '>{{ t(\'portfolio.addAsset\') }}<'],
      ['>资产分布<', '>{{ t(\'portfolio.assetDistribution\') }}<'],
      ['>系统设置<', '>{{ t(\'settings.title\') }}<'],
      ['>配置系统参数、API密钥和偏好设置<', '>{{ t(\'settings.subtitle\') }}<'],
      ['>需要重启服务才能生效<', '><span>{{ t(\'settings.restartRequired\') }}</span>'],
      ['>复制重启命令<', '>{{ t(\'settings.copyRestartCmd\') }}<'],
      ['>请输入<', '>:placeholder="t(\'common.pleaseInput\')"'],
      ['>请输入密钥<', '>:placeholder="t(\'common.pleaseInputKey\')"'],
      ['>请选择<', '>:placeholder="t(\'common.pleaseSelect\')"'],
      ['>默认:<', '>{{ t(\'settings.defaultValue\') }}<'],
      ['>重置<', '>{{ t(\'common.reset\') }}<'],
      ['>保存<', '>{{ t(\'common.save\') }}<'],
      ['>加载设置失败<', '>{{ t(\'settings.loadFailed\') }}<'],
      ['>保存成功<', '>{{ t(\'common.saveSuccess\') }}<'],
      ['>保存失败<', '>{{ t(\'common.saveFailed\') }}<'],
      ['>已复制到剪贴板<', '>{{ t(\'common.copied\') }}<'],
    ]

    for (const [from, to] of safeReplacements) {
      content = content.split(from).join(to)
    }

    // Replace specific attribute bindings
    content = content.replace(/title="复制地址"/g, ':title="t(\'billing.copyAddress\')"')
    content = content.replace(/title="复制金额"/g, ':title="t(\'billing.copyAmount\')"')
    content = content.replace(/placeholder="Username"/g, ':placeholder="t(\'user.login.username\')"')
    content = content.replace(/placeholder="Password"/g, ':placeholder="t(\'user.login.password\')"')
    content = content.replace(/placeholder="输入标的代码"/g, ':placeholder="t(\'aiAnalysis.inputSymbol\')"')
    content = content.replace(/placeholder="如 BTC\/USDT 或 AAPL"/g, ':placeholder="t(\'graphAnalysis.symbolPlaceholder\')"')
    content = content.replace(/placeholder="如 ETH\/USDT"/g, ':placeholder="t(\'graphAnalysis.symbolPlaceholder\')"')
    content = content.replace(/placeholder="事件唯一标识"/g, ':placeholder="t(\'graphAnalysis.eventUidPlaceholder\')"')
    content = content.replace(/placeholder="搜索用户名\/邮箱\/昵称"/g, ':placeholder="t(\'userManage.searchPlaceholder\')"')
    content = content.replace(/placeholder="搜索策略\/品种\/用户"/g, ':placeholder="t(\'userManage.strategySearchPlaceholder\')"')
    content = content.replace(/placeholder="搜索用户名"/g, ':placeholder="t(\'common.search\')"')
    content = content.replace(/placeholder="搜索用户名\/邮箱"/g, ':placeholder="t(\'userManage.searchPlaceholder\')"')

    if (content !== original) {
      fs.writeFileSync(file, content, 'utf-8')
      modifiedFiles++
      console.log('Modified:', path.relative(path.join(__dirname, '..'), file))
    }
  }
}

console.log(`\nTotal files scanned: ${totalFiles}`)
console.log(`Files modified: ${modifiedFiles}`)
