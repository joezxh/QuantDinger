<template>
  <div class="ai-analysis-page">
    <!-- Top Bar: Market Sentiment -->
    <div class="sentiment-bar">
      <div class="sentiment-item" v-if="sentiment.fear_greed">
        <span>{{ t('aiAnalysis.fearGreedIndex') }}</span>
        <span class="value" :class="sentimentClass(sentiment.fear_greed.value)">
          {{ sentiment.fear_greed.value }}
        </span>
      </div>
      <div class="sentiment-item" v-if="sentiment.vix">
        <span class="label">VIX</span>
        <span class="value">{{ sentiment.vix.value?.toFixed(2) }}</span>
      </div>
      <div class="sentiment-item" v-if="sentiment.dxy">
        <span>{{ t('aiAnalysis.dxy') }}</span>
        <span class="value">{{ sentiment.dxy.value?.toFixed(2) }}</span>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Panel: Heatmap & Calendar -->
      <div class="left-panel">
        <a-card :title="t('aiAnalysis.heatmap')" :bordered="false" class="panel-card">
          <a-tabs v-model:activeKey="heatmapType" size="small">
            <a-tab-pane key="crypto" :tab="t('market.crypto')" />
            <a-tab-pane key="commodities" :tab="t('market.commodities')" />
            <a-tab-pane key="sectors" :tab="t('market.sectors')" />
            <a-tab-pane key="forex" :tab="t('market.forex')" />
          </a-tabs>
          <div class="heatmap-container" v-if="heatmapData.length">
            <div v-for="item in heatmapData" :key="item.symbol" class="heatmap-item" :style="{ backgroundColor: getHeatmapColor(item.change) }">
              <div class="heatmap-symbol">{{ item.symbol }}</div>
              <div class="heatmap-change">{{ item.change?.toFixed(2) }}%</div>
            </div>
          </div>
          <a-spin v-else />
        </a-card>

        <a-card :title="t('aiAnalysis.economicCalendar')" :bordered="false" class="panel-card">
          <div class="calendar-list" v-if="calendarData.length">
            <div v-for="event in calendarData.slice(0, 10)" :key="event.id" class="calendar-item">
              <div class="calendar-time">{{ formatTime(event.time) }}</div>
              <div class="calendar-event">
                <a-tag :color="getImpactColor(event.impact)" size="small">{{ getImpactLabel(event.impact) }}</a-tag>
                <span class="event-name">{{ event.name }}</span>
              </div>
            </div>
          </div>
          <a-empty v-else :description="t('aiAnalysis.noCalendarData')" />
        </a-card>
      </div>

      <!-- Center Panel: AI Analysis -->
      <div class="center-panel">
        <a-card :bordered="false" class="analysis-card">
          <template #title>
            <div class="analysis-header">
              <span>{{ t('aiAnalysis.title') }}</span>
              <a-space>
                <a-select v-model:value="selectedMarket" style="width: 120px" @change="onMarketChange">
                  <a-select-option value="crypto">{{ t('market.crypto') }}</a-select-option>
                  <a-select-option value="stock">{{ t('aiAnalysis.selectOptionStock') }}</a-select-option>
                  <a-select-option value="forex">{{ t('market.forex') }}</a-select-option>
                  <a-select-option value="commodity">{{ t('aiAnalysis.selectOptionCommodity') }}</a-select-option>
                </a-select>
                <a-input-search
                  v-model:value="selectedSymbol"
                  :placeholder="t('aiAnalysis.inputSymbol')"
                  style="width: 150px"
                  @search="handleAnalyze"
                />
                <a-button type="primary" :loading="analyzing" @click="handleAnalyze">{{ t('aiAnalysis.startAnalysis') }}</a-button>
              </a-space>
            </div>
          </template>

          <!-- Analysis Result -->
          <div v-if="analysisResult" class="analysis-result">
            <a-card :bordered="false" class="result-card">
              <template #title>
                <div class="result-header">
                  <span>{{ selectedMarket }}: {{ selectedSymbol }}</span>
                  <a-tag :color="getStatusColor(analysisResult.status)">{{ getStatusLabel(analysisResult.status) }}</a-tag>
                </div>
              </template>
              <div class="result-content" v-html="analysisResult.content"></div>
              <div class="result-actions">
                <a-button size="small" @click="handleHistory">{{ t('indicatorIde.history') }}</a-button>
                <a-button size="small" type="primary" @click="handleAnalyze">{{ t('aiAnalysis.reAnalyze') }}</a-button>
              </div>
            </a-card>
          </div>

          <!-- Empty State -->
          <a-empty v-else :description="t('aiAnalysis.emptyHint')" class="empty-state" />
        </a-card>

        <!-- History Drawer -->
        <a-drawer
          v-model:visible="historyDrawerVisible"
          :title="t('aiAnalysis.analysisHistory')"
          width="400"
          placement="right"
        >
          <a-list :loading="historyLoading" :data-source="historyList">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>{{ item.market }}: {{ item.symbol }}</template>
                  <template #description>{{ formatDateTime(item.created_at) }}</template>
                </a-list-item-meta>
                <template #actions>
                  <a-button type="link" size="small" @click="viewHistory(item)">{{ t('common.view') }}</a-button>
                  <a-popconfirm :title="t('common.confirmDelete')" @confirm="deleteHistory(item.id)">
                    <a-button type="link" size="small" danger>{{ t('common.delete') }}</a-button>
                  </a-popconfirm>
                </template>
              </a-list-item>
            </template>
          </a-list>
          <a-pagination
            v-model:current="historyPage"
            :total="historyTotal"
            :pageSize="historyPageSize"
            simple
            class="history-pagination"
          />
        </a-drawer>
      </div>

      <!-- Right Panel: Watchlist -->
      <div class="right-panel">
        <a-card :bordered="false" class="watchlist-card">
          <template #title>
            <div class="watchlist-header">
              <span>{{ t('aiAnalysis.watchlist') }}</span>
              <a-button type="link" size="small" @click="showAddWatchlistModal">{{ t('common.add') }}</a-button>
            </div>
          </template>

          <a-list :loading="watchlistLoading" :data-source="watchlist" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <div class="watchlist-item">
                  <div class="watchlist-info">
                    <div class="symbol">{{ item.symbol }}</div>
                    <div class="name">{{ item.name }}</div>
                  </div>
                  <div class="watchlist-price">
                    <div class="price">{{ item.price?.toFixed(2) }}</div>
                    <div class="change" :class="changeClass(item.change)">{{ item.change?.toFixed(2) }}%</div>
                  </div>
                  <a-button type="link" size="small" danger @click="removeFromWatchlist(item)">{{ t('common.remove') }}</a-button>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <!-- Portfolio Summary -->
        <a-card :bordered="false" :title="t('portfolio.overview')" class="portfolio-card">
          <div class="portfolio-summary" v-if="portfolioSummary">
            <div class="portfolio-item">
              <span>{{ t('portfolio.totalPositions') }}</span>
              <span class="value">{{ portfolioSummary.total_positions }}</span>
            </div>
            <div class="portfolio-item">
              <span>{{ t('portfolio.totalPnl') }}</span>
              <span class="value" :class="pnlClass(portfolioSummary.total_pnl)">${{ portfolioSummary.total_pnl?.toFixed(2) }}</span>
            </div>
            <div class="portfolio-item">
              <span>{{ t('portfolio.monitorTasks') }}</span>
              <span class="value">{{ portfolioSummary.monitor_count }}</span>
            </div>
          </div>
          <a-empty v-else :description="t('portfolio.noPositions')" />
        </a-card>
      </div>
    </div>

    <!-- Add Watchlist Modal -->
    <a-modal
      v-model:visible="addWatchlistModalVisible"
      :title="t('aiAnalysis.addWatchlist')"
      @ok="handleAddWatchlist"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('common.market')">
          <a-select v-model:value="newWatchlistMarket">
            <a-select-option value="crypto">{{ t('market.crypto') }}</a-select-option>
            <a-select-option value="stock">{{ t('aiAnalysis.selectOptionStock') }}</a-select-option>
            <a-select-option value="forex">{{ t('market.forex') }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('aiAnalysis.symbolCode')">
          <a-input v-model:value="newWatchlistSymbol" :placeholder="t('aiAnalysis.symbolPlaceholder')" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import {
  getMarketSentiment,
  getMarketHeatmap,
  getEconomicCalendar,
} from '@/api/global-market'
import {
  getWatchlist,
  addWatchlist,
  removeWatchlist,
  getWatchlistPrices,
} from '@/api/market'
import {
  fastAnalyze,
  getAllAnalysisHistory,
  deleteAnalysisHistory as deleteHistoryApi,
} from '@/api/fast-analysis'
import {
  getPositions,
  getMonitors,
} from '@/api/portfolio'

interface SentimentData {
  fear_greed?: { value: number }
  vix?: { value: number }
  dxy?: { value: number }
}

interface HeatmapItem {
  symbol: string
  change: number
}

interface CalendarEvent {
  id: number
  time: string
  name: string
  impact: string
}

interface AnalysisResult {
  status: string
  content: string
}

interface HistoryItem {
  id: number
  market: string
  symbol: string
  created_at: string
}

interface WatchlistItem {
  symbol: string
  name: string
  price: number
  change: number
}

interface PortfolioSummary {
  total_positions: number
  total_pnl: number
  monitor_count: number
}

// State
const { t } = useI18n()
const sentiment = ref<SentimentData>({})
const heatmapType = ref('crypto')
const heatmapData = ref<HeatmapItem[]>([])
const calendarData = ref<CalendarEvent[]>([])

const selectedMarket = ref('crypto')
const selectedSymbol = ref('BTC')
const analyzing = ref(false)
const analysisResult = ref<AnalysisResult | null>(null)

const historyDrawerVisible = ref(false)
const historyLoading = ref(false)
const historyList = ref<HistoryItem[]>([])
const historyPage = ref(1)
const historyTotal = ref(0)
const historyPageSize = 10

const watchlist = ref<WatchlistItem[]>([])
const watchlistLoading = ref(false)
const addWatchlistModalVisible = ref(false)
const newWatchlistMarket = ref('crypto')
const newWatchlistSymbol = ref('')

const portfolioSummary = ref<PortfolioSummary | null>(null)

let priceRefreshTimer: number | null = null

// Methods
function sentimentClass(value: number): string {
  if (value < 25) return 'fear'
  if (value > 75) return 'greed'
  return 'neutral'
}

function getHeatmapColor(change: number): string {
  if (change > 0) return `rgba(82, 196, 26, ${Math.min(Math.abs(change) / 10, 0.8)})`
  if (change < 0) return `rgba(255, 77, 79, ${Math.min(Math.abs(change) / 10, 0.8)})`
  return 'rgba(140, 140, 140, 0.3)'
}

function formatTime(time: string): string {
  return time?.substring(11, 16) || ''
}

function getImpactColor(impact: string): string {
  const map: Record<string, string> = { high: 'red', medium: 'orange', low: 'blue' }
  return map[impact] || 'default'
}

function getImpactLabel(impact: string): string {
  const map: Record<string, string> = { high: t('impact.high'), medium: t('impact.medium'), low: t('impact.low') }
  return map[impact] || impact
}

function getStatusColor(status: string): string {
  const map: Record<string, string> = { completed: 'green', processing: 'blue', failed: 'red' }
  return map[status] || 'default'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = { completed: t('status.completed'), processing: t('status.processing'), failed: t('status.failed') }
  return map[status] || status
}

function changeClass(change: number): string {
  return change >= 0 ? 'positive' : 'negative'
}

function pnlClass(pnl: number): string {
  return pnl >= 0 ? 'profit' : 'loss'
}

function formatDateTime(date: string): string {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN')
}

async function loadSentiment() {
  try {
    const res = await getMarketSentiment()
    sentiment.value = res.data || {}
  } catch (e) {
    console.error('Failed to load sentiment:', e)
  }
}

async function loadHeatmap() {
  try {
    const res = await getMarketHeatmap()
    const data = res.data || {}
    heatmapData.value = data[heatmapType.value] || []
  } catch (e) {
    console.error('Failed to load heatmap:', e)
  }
}

async function loadCalendar() {
  try {
    const res = await getEconomicCalendar()
    calendarData.value = res.data || []
  } catch (e) {
    console.error('Failed to load calendar:', e)
  }
}

async function loadWatchlist() {
  watchlistLoading.value = true
  try {
    const res = await getWatchlist({})
    watchlist.value = (res.data || []).map((item: any) => ({
      symbol: item.symbol,
      name: item.name || item.symbol,
      price: 0,
      change: 0,
    }))
    await refreshPrices()
  } catch (e) {
    console.error('Failed to load watchlist:', e)
  }
  watchlistLoading.value = false
}

async function refreshPrices() {
  if (!watchlist.value.length) return
  try {
    const watchlistParam = watchlist.value.map((item) => ({
      market: selectedMarket.value,
      symbol: item.symbol,
    }))
    const res = await getWatchlistPrices({ watchlist: watchlistParam })
    const prices = res.data || {}
    watchlist.value.forEach((item) => {
      const priceData = prices[item.symbol]
      if (priceData) {
        item.price = priceData.price || 0
        item.change = priceData.change || 0
      }
    })
  } catch (e) {
    console.error('Failed to refresh prices:', e)
  }
}

async function handleAnalyze() {
  if (!selectedSymbol.value) {
    message.warning(t('validation.symbolRequired'))
    return
  }
  analyzing.value = true
  try {
    const res = await fastAnalyze({
      market: selectedMarket.value,
      symbol: selectedSymbol.value,
      language: 'zh',
    })
      if (res.code === 1) {
        analysisResult.value = {
          status: 'completed',
          content: res.data?.content || res.data?.report || t('aiAnalysis.analysisComplete'),
        }
        message.success(t('aiAnalysis.analysisComplete'))
      } else {
        message.error(res.msg || t('aiAnalysis.analysisFailed'))
      }
    } catch (e: any) {
      message.error(e.response?.data?.msg || t('aiAnalysis.analysisFailed'))
    }
  analyzing.value = false
}

function onMarketChange() {
  selectedSymbol.value = ''
  analysisResult.value = null
}

async function handleHistory() {
  historyDrawerVisible.value = true
  historyLoading.value = true
  try {
    const res = await getAllAnalysisHistory({
      page: historyPage.value,
      pagesize: historyPageSize,
    })
    historyList.value = res.data?.items || []
    historyTotal.value = res.data?.total || 0
  } catch (e) {
    message.error(t('aiAnalysis.loadHistoryFailed'))
  }
  historyLoading.value = false
}

async function viewHistory(item: HistoryItem) {
  analysisResult.value = {
    status: 'completed',
    content: item.market + ': ' + item.symbol,
  }
  historyDrawerVisible.value = false
}

async function deleteHistory(id: number) {
  try {
    await deleteHistoryApi(id)
    message.success('删除成功')
    handleHistory()
  } catch (e) {
    message.error(t('common.deleteFailed'))
  }
}

function showAddWatchlistModal() {
  addWatchlistModalVisible.value = true
}

async function handleAddWatchlist() {
  if (!newWatchlistSymbol.value) {
    message.warning(t('validation.symbolRequired'))
    return
  }
  try {
    await addWatchlist({
      market: newWatchlistMarket.value,
      symbol: newWatchlistSymbol.value,
    })
    message.success(t('aiAnalysis.addSuccess'))
    addWatchlistModalVisible.value = false
    loadWatchlist()
  } catch (e) {
    message.error(t('aiAnalysis.addFailed'))
  }
}

async function removeFromWatchlist(item: WatchlistItem) {
  try {
    await removeWatchlist({ symbol: item.symbol })
    message.success(t('aiAnalysis.removeSuccess'))
    loadWatchlist()
  } catch (e) {
    message.error(t('aiAnalysis.removeFailed'))
  }
}

async function loadPortfolio() {
  try {
    const [positionsRes, monitorsRes] = await Promise.all([
      getPositions({}),
      getMonitors(),
    ])
    const positions = positionsRes.data?.items || []
    const monitors = monitorsRes.data || []

    let totalPnl = 0
    positions.forEach((p: any) => {
      totalPnl += (p.current_value || 0) - (p.entry_price || 0) * (p.quantity || 0)
    })

    portfolioSummary.value = {
      total_positions: positions.length,
      total_pnl: totalPnl,
      monitor_count: monitors.length,
    }
  } catch (e) {
    console.error('Failed to load portfolio:', e)
  }
}

// Lifecycle
onMounted(() => {
  loadSentiment()
  loadHeatmap()
  loadCalendar()
  loadWatchlist()
  loadPortfolio()

  // Refresh prices every 30 seconds
  priceRefreshTimer = window.setInterval(refreshPrices, 30000)
})

onUnmounted(() => {
  if (priceRefreshTimer) {
    clearInterval(priceRefreshTimer)
  }
})
</script>

<style scoped>
.ai-analysis-page {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}

.sentiment-bar {
  display: flex;
  gap: 24px;
  padding: 16px 24px;
  margin-bottom: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.sentiment-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sentiment-item .label {
  font-size: 12px;
  color: #8c8c8c;
}

.sentiment-item .value {
  font-size: 20px;
  font-weight: 600;
}

.sentiment-item .value.fear {
  color: #ff4d4f;
}

.sentiment-item .value.greed {
  color: #52c41a;
}

.sentiment-item .value.neutral {
  color: #1890ff;
}

.main-content {
  display: grid;
  grid-template-columns: 300px 1fr 320px;
  gap: 20px;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-card,
.watchlist-card,
.portfolio-card,
.analysis-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.heatmap-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
  padding: 12px 0;
}

.heatmap-item {
  padding: 8px;
  border-radius: 4px;
  text-align: center;
  color: #fff;
  font-weight: 500;
}

.heatmap-symbol {
  font-size: 12px;
  margin-bottom: 4px;
}

.heatmap-change {
  font-size: 14px;
  font-weight: 600;
}

.calendar-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 0;
}

.calendar-item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.calendar-time {
  font-size: 12px;
  color: #8c8c8c;
  min-width: 50px;
}

.calendar-event {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-name {
  font-size: 14px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-card {
  margin-top: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-content {
  padding: 16px 0;
  line-height: 1.8;
}

.result-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.empty-state {
  padding: 60px 0;
}

.watchlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watchlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.watchlist-info {
  flex: 1;
}

.watchlist-info .symbol {
  font-weight: 600;
  font-size: 14px;
}

.watchlist-info .name {
  font-size: 12px;
  color: #8c8c8c;
}

.watchlist-price {
  text-align: right;
  margin-right: 12px;
}

.watchlist-price .price {
  font-weight: 600;
  font-size: 14px;
}

.watchlist-price .change {
  font-size: 12px;
}

.watchlist-price .change.positive {
  color: #52c41a;
}

.watchlist-price .change.negative {
  color: #ff4d4f;
}

.portfolio-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.portfolio-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.portfolio-item .label {
  color: #8c8c8c;
}

.portfolio-item .value {
  font-weight: 600;
}

.portfolio-item .value.profit {
  color: #52c41a;
}

.portfolio-item .value.loss {
  color: #ff4d4f;
}

.history-pagination {
  margin-top: 16px;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .left-panel,
  .right-panel {
    order: 2;
  }

  .center-panel {
    order: 1;
  }
}
</style>
