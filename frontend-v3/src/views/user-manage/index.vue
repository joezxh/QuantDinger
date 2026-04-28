<template>
  <div class="user-manage-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <TeamOutlined />
          <span>系统管理 & 用户运营</span>
        </h2>
        <p class="page-desc">全平台用户生命周期管理、策略运行监控及业务运营看板</p>
      </div>
    </div>

    <!-- Tabs Container -->
    <a-tabs v-model:activeKey="activeTab" @change="handleTabChange" class="manage-tabs">
      <!-- Tab 1: User Management -->
      <a-tab-pane key="users" tab="用户管理">
        <!-- User Summary Cards -->
        <div class="summary-cards" v-if="userSummary">
          <div class="summary-card glass-effect">
            <div class="card-icon blue"><TeamOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ userSummary.total_users || 0 }}</div>
              <div class="card-label">总用户数</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon green"><UserAddOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ userSummary.today_new || 0 }}</div>
              <div class="card-label">今日新增</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon yellow"><CrownOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ userSummary.active_vips || 0 }}</div>
              <div class="card-label">活跃VIP</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon purple"><WalletOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ formatLargeNumber(userSummary.total_credits) }}</div>
              <div class="card-label">全平台积分</div>
            </div>
          </div>
        </div>

        <!-- Toolbar -->
        <div class="toolbar">
          <div class="toolbar-left">
            <a-button type="primary" @click="showCreateModal">
              <UserAddOutlined />
              创建用户
            </a-button>
            <a-button :loading="exporting" @click="handleExport">
              <DownloadOutlined />
              导出用户
            </a-button>
            <a-button @click="loadUsers">
              <ReloadOutlined />
              刷新
            </a-button>
          </div>
          <div class="toolbar-right">
            <a-input-search
              v-model:value="searchKeyword"
              class="toolbar-search"
              placeholder="搜索用户名/邮箱/昵称"
              allowClear
              @search="handleSearch"
            />
          </div>
        </div>

        <!-- User Table -->
        <a-card :bordered="false" class="table-card">
          <a-table
            :columns="columns"
            :data-source="users"
            :loading="loading"
            :pagination="pagination"
            :row-key="(record: any) => record.id"
            :scroll="{ x: 1400 }"
            @change="handleTableChange"
          >
            <template #status="{ record }">
              <a-tag :color="record.status === 'active' ? 'green' : 'red'">
                {{ record.status === 'active' ? '启用' : '禁用' }}
              </a-tag>
            </template>

            <template #role="{ record }">
              <a-tag :color="getRoleColor(record.role)">
                {{ getRoleLabel(record.role) }}
              </a-tag>
            </template>

            <template #last_login_at="{ record }">
              <span v-if="record.last_login_at">{{ formatTime(record.last_login_at) }}</span>
              <span v-else class="text-muted">从未登录</span>
            </template>

            <template #credits="{ record }">
              <span class="credits-value">{{ formatCredits(record.credits) }}</span>
            </template>

            <template #vip_expires_at="{ record }">
              <template v-if="record.vip_expires_at && isVipActive(record.vip_expires_at)">
                <a-tag color="gold">
                  <CrownOutlined />
                  {{ formatDate(record.vip_expires_at) }}
                </a-tag>
              </template>
              <span v-else class="text-muted">-</span>
            </template>

            <template #register_ip="{ record }">
              <span v-if="record.register_ip">{{ record.register_ip }}</span>
              <span v-else class="text-muted">-</span>
            </template>

            <template #action="{ record }">
              <a-space>
                <a-tooltip title="编辑">
                  <a-button type="link" size="small" @click="showEditModal(record)">
                    <EditOutlined />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="积分">
                  <a-button type="link" size="small" @click="showCreditsModal(record)">
                    <WalletOutlined style="color: #722ed1" />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="角色">
                  <a-button type="link" size="small" @click="showAssignRoleModal(record)">
                    <SafetyOutlined style="color: #52c41a" />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="VIP">
                  <a-button type="link" size="small" @click="showVipModal(record)">
                    <CrownOutlined style="color: #faad14" />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="密码">
                  <a-button type="link" size="small" @click="showResetPasswordModal(record)">
                    <KeyOutlined />
                  </a-button>
                </a-tooltip>
                <a-popconfirm title="确定删除？" @confirm="handleDelete(record.id)">
                  <a-button type="link" size="small" :disabled="record.id === currentUserId">
                    <DeleteOutlined style="color: #ff4d4f" />
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- Tab 2: System Strategy Overview -->
      <a-tab-pane key="strategies" tab="系统实盘概览">
        <!-- Strategy Summary Cards -->
        <div class="summary-cards" v-if="strategySummary">
          <div class="summary-card glass-effect">
            <div class="card-icon blue"><FundOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ strategySummary.total_strategies || 0 }}</div>
              <div class="card-label">总策略数</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon green"><PlayCircleOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ strategySummary.running_strategies || 0 }}</div>
              <div class="card-sub">实盘: {{ strategySummary.running_live_strategies || 0 }} / 仅信号: {{ strategySummary.running_signal_strategies || 0 }}</div>
              <div class="card-label">运行中</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon orange"><DollarOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ formatLargeNumber(strategySummary.total_capital) }}</div>
              <div class="card-sub">实盘: {{ formatLargeNumber(strategySummary.live_capital) }} / 仅信号: {{ formatLargeNumber(strategySummary.signal_capital) }}</div>
              <div class="card-label">总保证金 (USDT)</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon" :class="(strategySummary.total_pnl || 0) >= 0 ? 'profit' : 'loss'"><RiseOutlined /></div>
            <div class="card-content">
              <div class="card-value" :class="(strategySummary.total_pnl || 0) >= 0 ? 'text-profit' : 'text-loss'">
                {{ formatPnl(strategySummary.total_pnl) }}
                <span class="roi-badge">{{ strategySummary.total_roi || 0 }}%</span>
              </div>
              <div class="card-sub">实盘: {{ formatPnl(strategySummary.live_pnl) }} / 仅信号: {{ formatPnl(strategySummary.signal_pnl) }}</div>
              <div class="card-label">总盈亏</div>
            </div>
          </div>
        </div>

        <!-- Strategy Toolbar -->
        <div class="toolbar">
          <div class="toolbar-left">
            <a-button @click="loadSystemStrategies"><ReloadOutlined /> 刷新</a-button>
            <a-select v-model:value="strategyStatusFilter" class="toolbar-select" @change="handleStrategyFilterChange">
              <a-select-option value="all">所有状态</a-select-option>
              <a-select-option value="running">运行中</a-select-option>
              <a-select-option value="stopped">已停止</a-select-option>
            </a-select>
            <a-select v-model:value="strategyExecutionFilter" class="toolbar-select" @change="handleStrategyExecutionFilterChange">
              <a-select-option value="all">所有执行模式</a-select-option>
              <a-select-option value="live">实盘托管</a-select-option>
              <a-select-option value="signal">仅信号通知</a-select-option>
            </a-select>
          </div>
          <div class="toolbar-right">
            <a-input-search
              v-model:value="strategySearchKeyword"
              class="toolbar-search"
              placeholder="搜索策略/品种/用户"
              allowClear
              @search="handleStrategySearch"
            />
          </div>
        </div>

        <!-- Strategy Table -->
        <a-card :bordered="false" class="table-card">
          <a-table
            :columns="strategyColumns"
            :data-source="systemStrategies"
            :loading="strategyLoading"
            :pagination="strategyPagination"
            :row-key="(record: any) => record.id"
            :scroll="{ x: 1800 }"
            size="small"
            @change="handleStrategyTableChange"
          >
            <template #strategyStatus="{ text }">
              <a-badge :status="text === 'running' ? 'processing' : 'default'" :text="text === 'running' ? '运行中' : '已停止'" />
            </template>
            <template #userInfo="{ record }">
              <div class="user-cell">
                <a-avatar size="small" :style="{ backgroundColor: getUserColor(record.user_id) }">
                  {{ (record.nickname || record.username || '?').charAt(0).toUpperCase() }}
                </a-avatar>
                <span class="user-name">{{ record.nickname || record.username }}</span>
              </div>
            </template>
            <template #pnlInfo="{ record }">
              <div :class="record.total_pnl >= 0 ? 'text-profit' : 'text-loss'">
                <div class="pnl-main">{{ formatPnl(record.total_pnl) }} ({{ record.roi }}%)</div>
                <div class="pnl-sub text-muted">已实现: {{ formatPnl(record.total_realized_pnl) }} / 未实现: {{ formatPnl(record.total_unrealized_pnl) }}</div>
              </div>
            </template>
            <template #executionModeInfo="{ text }">
              <a-tag :color="text === 'live' ? 'green' : 'blue'">{{ text === 'live' ? '实盘' : '信号' }}</a-tag>
            </template>
            <template #equityInfo="{ record }">
              <span v-if="record.execution_mode === 'live'">{{ formatLargeNumber(record.position_equity || 0) }}</span>
              <span v-else class="text-muted">—</span>
            </template>
            <template #indicatorInfo="{ text }">
              <a-tooltip v-if="text" :title="text">
                <span class="truncate-text">{{ text }}</span>
              </a-tooltip>
              <span v-else class="text-muted">-</span>
            </template>
            <template #leverageInfo="{ text }">
              <span v-if="text > 1" style="color: #fa8c16; font-weight: 600">{{ text }}x</span>
              <span v-else>{{ text || 1 }}x</span>
            </template>
            <template #timeframeInfo="{ text }">
              <a-tag v-if="text" size="small">{{ text }}</a-tag>
              <span v-else class="text-muted">-</span>
            </template>
            <template #createdAtInfo="{ text }">
              {{ formatTime(text) }}
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- Tab 3: Order List -->
      <a-tab-pane key="orders" tab="充值订单管理">
        <!-- Order Summary Cards -->
        <div class="summary-cards" v-if="orderSummary">
          <div class="summary-card glass-effect">
            <div class="card-icon purple"><FileTextOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ orderSummary.total_orders || 0 }}</div>
              <div class="card-label">总订单数</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon green"><CheckCircleOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ orderSummary.paid_orders || 0 }}</div>
              <div class="card-label">已支付</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon yellow"><ClockCircleOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ orderSummary.pending_orders || 0 }}</div>
              <div class="card-label">待处理</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon orange"><DollarOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ formatLargeNumber(orderSummary.total_revenue) }} <span class="unit">USDT</span></div>
              <div class="card-label">总收入</div>
            </div>
          </div>
        </div>

        <div class="toolbar">
          <div class="toolbar-left">
            <a-button @click="loadOrders"><ReloadOutlined /> 刷新</a-button>
            <a-select v-model:value="orderStatusFilter" class="toolbar-select" @change="handleOrderFilterChange">
              <a-select-option value="all">所有状态</a-select-option>
              <a-select-option value="pending">待支付</a-select-option>
              <a-select-option value="paid">已支付</a-select-option>
              <a-select-option value="confirmed">已完成</a-select-option>
              <a-select-option value="expired">已过期</a-select-option>
            </a-select>
          </div>
          <div class="toolbar-right">
            <a-input-search
              v-model:value="orderSearchKeyword"
              class="toolbar-search"
              placeholder="搜索用户名/邮箱"
              allowClear
              @search="handleOrderSearch"
            />
          </div>
        </div>

        <a-card :bordered="false" class="table-card">
          <a-table
            :columns="orderColumns"
            :data-source="orders"
            :loading="orderLoading"
            :pagination="orderPagination"
            :row-key="(record: any) => record.id"
            :scroll="{ x: 1400 }"
            @change="handleOrderTableChange"
          >
            <template #orderUserInfo="{ record }">
              <div class="user-cell">
                <a-avatar size="small" :style="{ backgroundColor: getUserColor(record.user_id) }">
                  {{ (record.nickname || record.username || '?').charAt(0).toUpperCase() }}
                </a-avatar>
                <span class="user-name">{{ record.nickname || record.username }}</span>
              </div>
            </template>
            <template #orderStatusInfo="{ text }">
              <a-tag :color="getOrderStatusColor(text)">{{ getOrderStatusLabel(text) }}</a-tag>
            </template>
            <template #amountInfo="{ record }">
              <span class="amount-val">{{ record.amount }}</span>
              <span class="currency-label">{{ record.currency }}</span>
            </template>
            <template #addressInfo="{ text }">
              <a-tooltip v-if="text" :title="text">
                <span class="truncate-text" style="width: 120px">{{ text }}</span>
              </a-tooltip>
              <span v-else class="text-muted">-</span>
            </template>
            <template #txHashInfo="{ text }">
              <a-tooltip v-if="text" :title="text">
                <span class="truncate-text" style="width: 140px">{{ text }}</span>
              </a-tooltip>
              <span v-else class="text-muted">-</span>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- Tab 4: AI Analysis Records -->
      <a-tab-pane key="aiStats" tab="AI分析运营">
        <!-- AI Stats Summary Cards -->
        <div class="summary-cards" v-if="aiStatsSummary">
          <div class="summary-card glass-effect">
            <div class="card-icon cyan"><ThunderboltOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ aiStatsSummary.total_analyses || 0 }}</div>
              <div class="card-label">总分析次数</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon blue"><TeamOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ aiStatsSummary.unique_users || 0 }}</div>
              <div class="card-label">活跃分析用户</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon orange"><BarChartOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ aiStatsSummary.unique_symbols || 0 }}</div>
              <div class="card-label">覆盖代币数</div>
            </div>
          </div>
          <div class="summary-card glass-effect">
            <div class="card-icon green"><LikeOutlined /></div>
            <div class="card-content">
              <div class="card-value">{{ aiStatsSummary.correct_count || 0 }} <span class="divider">/</span> {{ aiStatsSummary.total_memory || 0 }}</div>
              <div class="card-label">AI准确率 (验证通过/总记忆)</div>
            </div>
          </div>
        </div>

        <div class="toolbar">
          <div class="toolbar-left">
            <a-button @click="loadAiStats"><ReloadOutlined /> 刷新</a-button>
          </div>
          <div class="toolbar-right">
            <a-input-search
              v-model:value="aiStatsSearchKeyword"
              class="toolbar-search"
              placeholder="搜索用户名"
              allowClear
              @search="handleAiStatsSearch"
            />
          </div>
        </div>

        <div class="ai-stats-grid">
          <a-card title="用户分析排行" :bordered="false" class="table-card glass-effect">
            <a-table
              :columns="aiUserColumns"
              :data-source="aiUserStats"
              :loading="aiStatsLoading"
              :pagination="aiStatsPagination"
              :row-key="(record: any) => record.user_id"
              size="small"
              @change="handleAiStatsTableChange"
            >
              <template #aiUserInfo="{ record }">
                <div class="user-cell">
                  <a-avatar size="small" :style="{ backgroundColor: getUserColor(record.user_id) }">
                    {{ (record.nickname || record.username || '?').charAt(0).toUpperCase() }}
                  </a-avatar>
                  <span class="user-name">{{ record.nickname || record.username }}</span>
                </div>
              </template>
              <template #accuracyInfo="{ record }">
                <span class="text-profit">{{ record.correct || 0 }}</span> / <span class="text-loss">{{ record.incorrect || 0 }}</span>
              </template>
              <template #feedbackInfo="{ record }">
                <span style="color: #52c41a;"><LikeOutlined /> {{ record.helpful || 0 }}</span>
                <span class="text-muted"> / </span>
                <span style="color: #ff4d4f;"><DislikeOutlined /> {{ record.not_helpful || 0 }}</span>
              </template>
              <template #lastAnalysisAt="{ text }">
                {{ formatTime(text) }}
              </template>
            </a-table>
          </a-card>

          <a-card title="最近分析记录" :bordered="false" class="table-card glass-effect">
            <a-table
              :columns="aiRecentColumns"
              :data-source="aiRecentRecords"
              :loading="aiStatsLoading"
              :pagination="false"
              :row-key="(record: any) => record.id"
              size="small"
            >
              <template #recentStatusInfo="{ text }">
                <a-tag :color="text === 'completed' ? 'green' : 'red'">{{ text }}</a-tag>
              </template>
              <template #recentCreatedAt="{ text }">
                {{ formatTime(text) }}
              </template>
            </a-table>
          </a-card>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- Modal sections (Keep existing) -->
    <a-modal v-model:open="modalVisible" :title="isEdit ? '编辑用户' : '创建用户'" :confirmLoading="modalLoading" @ok="handleModalOk" @cancel="handleModalCancel">
      <a-form :model="form" layout="vertical">
        <a-form-item label="用户名"><a-input v-model:value="form.username" :disabled="isEdit" placeholder="请输入用户名"><template #prefix><UserOutlined /></template></a-input></a-form-item>
        <a-form-item v-if="!isEdit" label="密码"><a-input-password v-model:value="form.password" placeholder="请输入密码（至少6位）"><template #prefix><LockOutlined /></template></a-input-password></a-form-item>
        <a-form-item label="昵称"><a-input v-model:value="form.nickname" placeholder="请输入昵称"><template #prefix><SmileOutlined /></template></a-input></a-form-item>
        <a-form-item label="邮箱"><a-input v-model:value="form.email" type="email" placeholder="请输入邮箱"><template #prefix><MailOutlined /></template></a-input></a-form-item>
        <a-form-item label="角色"><a-select v-model:value="form.role" placeholder="选择角色"><a-select-option v-for="role in roles" :key="role.id" :value="role.id">{{ getRoleLabel(role.id) }}</a-select-option></a-select></a-form-item>
        <a-form-item v-if="isEdit" label="状态"><a-select v-model:value="form.status"><a-select-option value="active">启用</a-select-option><a-select-option value="disabled">禁用</a-select-option></a-select></a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="resetPasswordVisible" title="重置密码" :confirmLoading="resetPasswordLoading" @ok="handleResetPassword">
      <a-alert message="此操作将重置用户密码" type="warning" showIcon />
      <a-form :model="resetPasswordForm" layout="vertical" style="margin-top: 16px"><a-form-item label="新密码"><a-input-password v-model:value="resetPasswordForm.new_password" placeholder="请输入新密码（至少6位）"><template #prefix><LockOutlined /></template></a-input-password></a-form-item></a-form>
    </a-modal>

    <a-modal v-model:open="creditsModalVisible" :title="'调整积分' + (creditsEditingUser ? ` - ${creditsEditingUser.username}` : '')" :confirmLoading="creditsLoading" @ok="handleSetCredits">
      <div class="current-credits-info" v-if="creditsEditingUser"><span class="label">当前积分:</span><span class="value">{{ formatCredits(creditsEditingUser.credits) }}</span></div>
      <a-form layout="vertical" style="margin-top: 16px"><a-form-item label="新积分"><a-input-number v-model:value="newCredits" :min="0" :precision="2" style="width: 100%" placeholder="请输入新积分" /></a-form-item><a-form-item label="备注"><a-input v-model:value="creditsRemark" placeholder="可选备注信息" /></a-form-item></a-form>
    </a-modal>

    <a-modal v-model:open="vipModalVisible" :title="'设置VIP' + (vipEditingUser ? ` - ${vipEditingUser.username}` : '')" :confirmLoading="vipLoading" @ok="handleSetVip">
      <a-form layout="vertical" style="margin-top: 16px">
        <a-form-item label="VIP天数">
          <a-select v-model:value="vipDays" style="width: 100%"><a-select-option :value="0">取消VIP</a-select-option><a-select-option :value="7">7天</a-select-option><a-select-option :value="30">30天</a-select-option><a-select-option :value="90">90天</a-select-option><a-select-option :value="180">180天</a-select-option><a-select-option :value="365">365天</a-select-option><a-select-option :value="-1">自定义日期</a-select-option></a-select>
        </a-form-item>
        <a-form-item v-if="vipDays === -1" label="到期时间"><a-date-picker v-model:value="vipCustomDate" show-time format="YYYY-MM-DD HH:mm:ss" style="width: 100%" /></a-form-item>
        <a-form-item label="备注"><a-input v-model:value="vipRemark" placeholder="可选备注信息" /></a-form-item>
      </a-form>
    </a-modal>

    <!-- 角色分配弹窗 -->
    <a-modal
      v-model:visible="roleModalVisible"
      title="分配角色"
      :confirm-loading="roleSaving"
      @ok="handleAssignRoles"
    >
      <div v-if="roleEditingUser" style="margin-bottom: 16px">
        正在为用户 <a-tag color="blue">{{ roleEditingUser.username }}</a-tag> 分配角色
      </div>
      <a-checkbox-group v-model:value="selectedRoleIds" style="width: 100%">
        <a-row>
          <a-col v-for="role in availableRoles" :key="role.id" :span="12" style="margin-bottom: 8px">
            <a-checkbox :value="role.id">
              {{ role.name }}
              <span v-if="role.description" style="color: #999; font-size: 12px">({{ role.description }})</span>
            </a-checkbox>
          </a-col>
        </a-row>
      </a-checkbox-group>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import dayjs, { Dayjs } from 'dayjs'
import {
  TeamOutlined, UserAddOutlined, DownloadOutlined, ReloadOutlined, EditOutlined, DeleteOutlined, WalletOutlined, 
  CrownOutlined, KeyOutlined, UserOutlined, LockOutlined, SmileOutlined, MailOutlined, FundOutlined, PlayCircleOutlined,
  DollarOutlined, RiseOutlined, FileTextOutlined, CheckCircleOutlined, ClockCircleOutlined, ThunderboltOutlined,
  BarChartOutlined, LikeOutlined, HistoryOutlined, DislikeOutlined, SafetyOutlined
} from '@ant-design/icons-vue'
import {
  getUserList, exportUsers, createUser, updateUser, deleteUser, resetUserPassword, getRoles, 
  setUserCredits, setUserVip, getSystemStrategies, getAdminOrders, getAdminAiStats,
  getAllRoles, getUserRoles, assignRolesToUser
} from '@/api/user'
import { useUserStore } from '@/stores/user'

// Types
interface User { id: number; username: string; nickname: string; email: string; role: string; status: string; credits: number; vip_expires_at: string; last_login_at: string; register_ip: string; }
interface Role { id: string; name: string; }

const userStore = useUserStore()
const activeTab = ref('users')

// --- User Tab States ---
const loading = ref(false)
const exporting = ref(false)
const users = ref<User[]>([])
const userSummary = ref<any>(null)
const roles = ref<Role[]>([])
const searchKeyword = ref('')
const pagination = reactive({ current: 1, pageSize: 10, total: 0, showSizeChanger: true, showTotal: (total: number) => `共 ${total} 条` })
const modalVisible = ref(false)
const modalLoading = ref(false)
const isEdit = ref(false)
const editingUser = ref<User | null>(null)
const form = reactive({ username: '', password: '', nickname: '', email: '', role: 'user', status: 'active' })
const resetPasswordVisible = ref(false)
const resetPasswordLoading = ref(false)
const resetPasswordUserId = ref<number | null>(null)
const resetPasswordForm = reactive({ new_password: '' })
const creditsModalVisible = ref(false)
const creditsLoading = ref(false)
const creditsEditingUser = ref<User | null>(null)
const newCredits = ref(0)
const creditsRemark = ref('')
const vipModalVisible = ref(false)
const vipLoading = ref(false)
const vipEditingUser = ref<User | null>(null)
const vipDays = ref(30)
const vipCustomDate = ref<Dayjs | null>(null)
const vipRemark = ref('')

// Role assignment
const roleModalVisible = ref(false)
const roleSaving = ref(false)
const roleEditingUser = ref<any>(null)
const availableRoles = ref<any[]>([])
const selectedRoleIds = ref<number[]>([])

const currentUserId = computed(() => userStore.userInfo?.id)

// --- Strategy Tab States ---
const strategyLoading = ref(false)
const systemStrategies = ref([])
const strategySummary = ref<any>(null)
const strategyStatusFilter = ref('all')
const strategyExecutionFilter = ref('all')
const strategySearchKeyword = ref('')
const strategyPagination = reactive({ current: 1, pageSize: 20, total: 0, showSizeChanger: true })
const strategySort = reactive({ field: '', order: 'desc' })

// --- Order Tab States ---
const orderLoading = ref(false)
const orders = ref([])
const orderSummary = ref<any>(null)
const orderStatusFilter = ref('all')
const orderSearchKeyword = ref('')
const orderPagination = reactive({ current: 1, pageSize: 20, total: 0 })

// --- AI Stats Tab States ---
const aiStatsLoading = ref(false)
const aiUserStats = ref([])
const aiRecentRecords = ref([])
const aiStatsSummary = ref<any>(null)
const aiStatsSearchKeyword = ref('')
const aiStatsPagination = reactive({ current: 1, pageSize: 20, total: 0 })

// --- Columns ---
const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '用户名', dataIndex: 'username', width: 120 },
  { title: '昵称', dataIndex: 'nickname', width: 100 },
  { title: '角色', dataIndex: 'role', width: 90, slots: { customRender: 'role' } },
  { title: '积分', dataIndex: 'credits', width: 100, slots: { customRender: 'credits' } },
  { title: 'VIP', dataIndex: 'vip_expires_at', width: 120, slots: { customRender: 'vip_expires_at' } },
  { title: '状态', dataIndex: 'status', width: 90, slots: { customRender: 'status' } },
  { title: '注册IP', dataIndex: 'register_ip', width: 120, slots: { customRender: 'register_ip' } },
  { title: '最后登录', dataIndex: 'last_login_at', width: 150, slots: { customRender: 'last_login_at' } },
  { title: '操作', key: 'action', width: 220, fixed: 'right', slots: { customRender: 'action' } },
]

const strategyColumns = [
  { title: 'ID', dataIndex: 'id', width: 70, fixed: 'left' },
  { title: '用户', key: 'userInfo', width: 120, fixed: 'left', slots: { customRender: 'userInfo' } },
  { title: '策略名称', dataIndex: 'strategy_name', width: 150 },
  { title: '状态', dataIndex: 'status', width: 100, slots: { customRender: 'strategyStatus' } },
  { title: '模式', dataIndex: 'execution_mode', width: 80, slots: { customRender: 'executionModeInfo' } },
  { title: '交易对', dataIndex: 'symbol', width: 120 },
  { title: '保证金', dataIndex: 'capital', width: 100, customRender: ({ text }) => formatLargeNumber(text) },
  { title: '当前权益', key: 'equityInfo', width: 100, slots: { customRender: 'equityInfo' } },
  { title: '盈亏 (USDT)', key: 'pnlInfo', width: 220, slots: { customRender: 'pnlInfo' } },
  { title: '指标', dataIndex: 'indicator_name', width: 140, slots: { customRender: 'indicatorInfo' } },
  { title: '交易所', dataIndex: 'exchange', width: 100 },
  { title: '周期', dataIndex: 'timeframe', width: 80, slots: { customRender: 'timeframeInfo' } },
  { title: '杠杆', dataIndex: 'leverage', width: 70, slots: { customRender: 'leverageInfo' } },
  { title: '运行时间', dataIndex: 'uptime', width: 120 },
  { title: '创建时间', dataIndex: 'created_at', width: 160, slots: { customRender: 'createdAtInfo' } },
]

const orderColumns = [
  { title: '用户', key: 'orderUserInfo', width: 140, slots: { customRender: 'orderUserInfo' } },
  { title: '类型', dataIndex: 'order_type', width: 90 },
  { title: '套餐', dataIndex: 'plan', width: 100, customRender: ({ text }) => text || '-' },
  { title: '金额', key: 'amountInfo', width: 120, slots: { customRender: 'amountInfo' } },
  { title: '网络', dataIndex: 'chain', width: 90 },
  { title: '充值地址', dataIndex: 'address', width: 140, slots: { customRender: 'addressInfo' } },
  { title: '交易哈希', dataIndex: 'tx_hash', width: 160, slots: { customRender: 'txHashInfo' } },
  { title: '状态', dataIndex: 'status', width: 100, slots: { customRender: 'orderStatusInfo' } },
  { title: '时间', dataIndex: 'created_at', width: 160, customRender: ({ text }) => formatTime(text) },
]

const aiUserColumns = [
  { title: '用户', key: 'aiUserInfo', width: 140, slots: { customRender: 'aiUserInfo' } },
  { title: '分析次数', dataIndex: 'analysis_count', width: 100, align: 'center' },
  { title: '准确率 (对/错)', key: 'accuracyInfo', width: 140, align: 'center', slots: { customRender: 'accuracyInfo' } },
  { title: '反馈 (赞/踩)', key: 'feedbackInfo', width: 120, align: 'center', slots: { customRender: 'feedbackInfo' } },
  { title: '最后分析时间', dataIndex: 'last_analysis_at', width: 160, slots: { customRender: 'lastAnalysisAt' } },
]

const aiRecentColumns = [
  { title: '用户', key: 'aiUserInfo', width: 120, slots: { customRender: 'aiUserInfo' } },
  { title: '品种', dataIndex: 'symbol', width: 100 },
  { title: '状态', dataIndex: 'status', width: 100, slots: { customRender: 'recentStatusInfo' } },
  { title: '时间', dataIndex: 'created_at', width: 160, slots: { customRender: 'recentCreatedAt' } },
]

// --- Logic ---
const handleTabChange = (key) => {
  if (key === 'strategies') loadSystemStrategies()
  else if (key === 'orders') loadOrders()
  else if (key === 'aiStats') loadAiStats()
  else loadUsers()
}

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchKeyword.value,
    })
    if (res.code === 1) {
      users.value = res.data.items || []
      pagination.total = res.data.total || 0
      userSummary.value = res.data.summary || null
    }
  } finally {
    loading.value = false
  }
}

const loadSystemStrategies = async () => {
  strategyLoading.value = true
  try {
    const res = await getSystemStrategies({
      page: strategyPagination.current, page_size: strategyPagination.pageSize,
      status: strategyStatusFilter.value === 'all' ? '' : strategyStatusFilter.value,
      execution_mode: strategyExecutionFilter.value === 'all' ? '' : strategyExecutionFilter.value,
      search: strategySearchKeyword.value
    })
    if (res.code === 1 && res.data) {
      systemStrategies.value = res.data.items || []
      strategyPagination.total = res.data.total || 0
      strategySummary.value = res.data.summary
    }
  } catch (e) { message.error('策略概览加载失败') }
  strategyLoading.value = false
}

const loadOrders = async () => {
  orderLoading.value = true
  try {
    const res = await getAdminOrders({
      page: orderPagination.current, page_size: orderPagination.pageSize,
      status: orderStatusFilter.value === 'all' ? '' : orderStatusFilter.value,
      search: orderSearchKeyword.value
    })
    if (res.code === 1 && res.data) {
      orders.value = res.data.items || []
      orderPagination.total = res.data.total || 0
      orderSummary.value = res.data.summary
    }
  } catch (e) { message.error('订单加载失败') }
  orderLoading.value = false
}

const loadAiStats = async () => {
  aiStatsLoading.value = true
  try {
    const res = await getAdminAiStats({
      page: aiStatsPagination.current, page_size: aiStatsPagination.pageSize,
      search: aiStatsSearchKeyword.value
    })
    if (res.code === 1 && res.data) {
      aiUserStats.value = res.data.user_stats || []
      aiRecentRecords.value = res.data.recent_records || []
      aiStatsSummary.value = res.data.summary
      aiStatsPagination.total = res.data.total || 0
    }
  } catch (e) { message.error('AI统计加载失败') }
  aiStatsLoading.value = false
}

// Helpers
const getRoleColor = (role) => ({ admin: 'red', manager: 'orange', user: 'blue' }[role] || 'default')
const getRoleLabel = (role) => ({ admin: '管理员', manager: '经理', user: '用户' }[role] || role)
const formatTime = (t) => t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : ''
const formatDate = (t) => t ? dayjs(t).format('YYYY-MM-DD') : ''
const formatCredits = (c) => Number(c || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
const formatPnl = (p) => (p >= 0 ? '+' : '') + Number(p || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
const formatLargeNumber = (n) => Number(n || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })
const isVipActive = (e) => dayjs(e).isAfter(dayjs())
const getUserColor = (id) => ['#1890ff', '#722ed1', '#13c2c2', '#fa8c16', '#eb2f96', '#52c41a', '#2f54eb', '#faad14'][(id || 0) % 8]
const getOrderStatusColor = (s) => ({ paid: 'green', confirmed: 'blue', pending: 'orange', expired: 'red' }[s] || 'default')
const getOrderStatusLabel = (s) => ({ paid: '已支付', confirmed: '已完成', pending: '待处理', expired: '已过期' }[s] || s)

// Handlers
const handleSearch = () => { pagination.current = 1; loadUsers() }
const handleTableChange = (pag) => { pagination.current = pag.current; pagination.pageSize = pag.pageSize; loadUsers() }
const handleStrategySearch = () => { strategyPagination.current = 1; loadSystemStrategies() }
const handleStrategyFilterChange = () => { strategyPagination.current = 1; loadSystemStrategies() }
const handleStrategyExecutionFilterChange = () => { strategyPagination.current = 1; loadSystemStrategies() }
const handleStrategyTableChange = (pag) => { strategyPagination.current = pag.current; loadSystemStrategies() }
const handleOrderSearch = () => { orderPagination.current = 1; loadOrders() }
const handleOrderFilterChange = () => { orderPagination.current = 1; loadOrders() }
const handleOrderTableChange = (pag) => { orderPagination.current = pag.current; loadOrders() }
const handleAiStatsSearch = () => { aiStatsPagination.current = 1; loadAiStats() }
const handleAiStatsTableChange = (pag) => { aiStatsPagination.current = pag.current; loadAiStats() }

// CRUD Modals
const showCreateModal = () => { isEdit.value = false; Object.assign(form, { username: '', password: '', nickname: '', email: '', role: 'user', status: 'active' }); modalVisible.value = true }
const showEditModal = (u) => { isEdit.value = true; editingUser.value = u; Object.assign(form, { username: u.username, nickname: u.nickname, email: u.email, role: u.role, status: u.status }); modalVisible.value = true }
const handleModalOk = async () => { modalLoading.value = true; try { if (isEdit.value && editingUser.value) { await updateUser(editingUser.value.id, form); message.success('更新成功') } else { await createUser(form); message.success('创建成功') }; modalVisible.value = false; loadUsers() } catch (e) { message.error('操作失败') }; modalLoading.value = false }
const handleModalCancel = () => { modalVisible.value = false }
const handleDelete = async (id) => { try { await deleteUser(id); message.success('已删除'); loadUsers() } catch (e) { message.error('删除失败') } }
const showResetPasswordModal = (u) => { resetPasswordUserId.value = u.id; resetPasswordForm.new_password = ''; resetPasswordVisible.value = true }
const handleResetPassword = async () => { try { await resetUserPassword({ user_id: resetPasswordUserId.value!, new_password: resetPasswordForm.new_password }); message.success('密码已重置'); resetPasswordVisible.value = false } catch (e) { message.error('重置失败') } }
const showCreditsModal = (u) => { creditsEditingUser.value = u; newCredits.value = u.credits; creditsRemark.value = ''; creditsModalVisible.value = true }
const handleSetCredits = async () => { try { await setUserCredits({ user_id: creditsEditingUser.value!.id, credits: newCredits.value, remark: creditsRemark.value }); message.success('积分已更新'); creditsModalVisible.value = false; loadUsers() } catch (e) { message.error('更新失败') } }
const showVipModal = (u) => { vipEditingUser.value = u; vipDays.value = 30; vipCustomDate.value = null; vipRemark.value = ''; vipModalVisible.value = true }

const handleSetVip = async () => {
  const data: any = {
    user_id: vipEditingUser.value!.id,
    remark: vipRemark.value,
  }

  if (vipDays.value === -1) {
    if (!vipCustomDate.value) {
      message.error('请选择日期')
      return
    }
    data.vip_expires_at = vipCustomDate.value.toISOString()
  } else {
    data.vip_days = vipDays.value
  }

  vipLoading.value = true
  try {
    const res = await setUserVip(data)
    if (res.code === 1) {
      message.success('VIP设置成功')
      vipModalVisible.value = false
      loadUsers()
    }
  } finally {
    vipLoading.value = false
  }
}

// Role assignment
const showAssignRoleModal = async (record: any) => {
  roleEditingUser.value = record
  roleModalVisible.value = true
  try {
    const [rolesRes, userRolesRes] = await Promise.all([
      getAllRoles(),
      getUserRoles(record.id)
    ])
    availableRoles.value = rolesRes.data || []
    selectedRoleIds.value = (userRolesRes.data || []).map((r: any) => r.id)
  } catch (error) {
    message.error('加载角色数据失败')
  }
}

const handleAssignRoles = async () => {
  if (!roleEditingUser.value) return
  
  roleSaving.value = true
  try {
    const res = await assignRolesToUser(roleEditingUser.value.id, selectedRoleIds.value)
    if (res.code === 1) {
      message.success('角色分配成功')
      roleModalVisible.value = false
      loadUsers()
    }
  } finally {
    roleSaving.value = false
  }
}

const loadRoles = async () => { try { const res = await getRoles(); if (res.code === 1) roles.value = res.data.roles || [] } catch (e) {} }
const handleExport = async () => { exporting.value = true; try { const blob = await exportUsers({ search: searchKeyword.value }); const url = window.URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `users_${dayjs().format('YYYYMMDD')}.csv`; link.click(); message.success('导出成功') } catch (e) { message.error('导出失败') }; exporting.value = false }

onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<style scoped lang="less">
.user-manage-page {
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);
  transition: background 0.3s;
}

:deep(.ant-layout-content) {
  padding: 0 !important;
}

.dark .user-manage-page,
.realdark .user-manage-page {
  background: #000;
}

.page-header {
  margin-bottom: 24px;
  .page-title {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: #001529;
    .anticon { color: #1890ff; }
  }
  .page-desc { color: #8c8c8c; margin: 0; }
}

.manage-tabs {
  background: transparent;
  :deep(.ant-tabs-nav) {
    background: #fff;
    padding: 0 24px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  :deep(.ant-tabs-content-holder) {
    background: transparent;
  }
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 16px 0 24px;
}

.summary-card {
  padding: 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s;
  
  &:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
  
  .card-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: #fff;
    
    &.blue { background: linear-gradient(135deg, #1890ff, #36cfc9); }
    &.green { background: linear-gradient(135deg, #52c41a, #95de64); }
    &.orange { background: linear-gradient(135deg, #fa8c16, #ffd666); }
    &.profit { background: linear-gradient(135deg, #52c41a, #b7eb8f); }
    &.loss { background: linear-gradient(135deg, #ff4d4f, #ffbb96); }
    &.purple { background: linear-gradient(135deg, #722ed1, #b37feb); }
    &.yellow { background: linear-gradient(135deg, #fadb14, #fffb8f); }
    &.cyan { background: linear-gradient(135deg, #13c2c2, #5cdbd3); }
  }
  
  .card-content {
    flex: 1;
    .card-value { font-size: 22px; font-weight: 700; color: #262626; line-height: 1.2; }
    .card-label { font-size: 13px; color: #8c8c8c; margin-top: 4px; }
    .card-sub { font-size: 12px; color: #bfbfbf; margin-top: 2px; }
    .roi-badge { font-size: 12px; padding: 2px 6px; border-radius: 4px; background: rgba(0,0,0,0.05); margin-left: 8px; font-weight: normal; }
  }
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin: 16px 0;
  padding: 0 4px;
  .toolbar-left { display: flex; gap: 8px; }
  .toolbar-select { width: 150px; }
  .toolbar-search { width: 280px; }
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.glass-effect {
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.dark .glass-effect,
.realdark .glass-effect {
  background: rgba(30, 30, 30, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.dark .table-card,
.realdark .table-card {
  background: #141414;
  border: 1px solid #303030;
}

.dark .page-title,
.realdark .page-title {
  color: #fff;
}

.dark .card-value,
.realdark .card-value {
  color: #eee !important;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  .user-name { font-weight: 500; }
}

.text-profit { color: #52c41a; }
.text-loss { color: #ff4d4f; }
.text-muted { color: #8c8c8c; }
.credits-value { font-weight: 600; color: #722ed1; }

.ai-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.current-credits-info {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  .label { color: #8c8c8c; margin-right: 8px; }
  .value { font-weight: 600; color: #722ed1; }
}

.truncate-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.pnl-main { font-weight: 600; }
.pnl-sub { font-size: 11px; margin-top: 2px; }

@media (max-width: 1200px) {
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
  .ai-stats-grid { grid-template-columns: 1fr; }
}
</style>
