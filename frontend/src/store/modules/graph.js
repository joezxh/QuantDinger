/**
 * Graph / Dify 状态管理模块
 * 管理图谱上下文、Dify 工作流列表、图谱质量等全局状态
 */
import {
  getGraphContext,
  getRelatedAssets,
  getRecentEvents,
  getGraphQuality,
  getContagionPath,
  getSmartMoney,
  getEventImpact
} from '@/api/graph'
import { getWorkflows } from '@/api/dify'

const graph = {
  state: {
    // 图谱上下文
    graphContext: null,
    graphContextLoading: false,
    graphContextError: '',

    // 关联资产
    relatedAssets: [],
    relatedAssetsLoading: false,

    // 近期事件
    recentEvents: [],
    recentEventsLoading: false,

    // 图谱质量
    graphQuality: null,
    graphQualityLoading: false,

    // Dify 工作流
    difyWorkflows: [],
    difyWorkflowsLoading: false,
    selectedWorkflowCode: '',

    // 传染路径
    contagionPath: null,
    contagionPathLoading: false,

    // 聪明钱信号
    smartMoney: null,
    smartMoneyLoading: false,

    // 事件影响链
    eventImpact: null,
    eventImpactLoading: false
  },

  mutations: {
    SET_GRAPH_CONTEXT (state, payload) {
      state.graphContext = payload
    },
    SET_GRAPH_CONTEXT_LOADING (state, payload) {
      state.graphContextLoading = payload
    },
    SET_GRAPH_CONTEXT_ERROR (state, payload) {
      state.graphContextError = payload
    },

    SET_RELATED_ASSETS (state, payload) {
      state.relatedAssets = payload
    },
    SET_RELATED_ASSETS_LOADING (state, payload) {
      state.relatedAssetsLoading = payload
    },

    SET_RECENT_EVENTS (state, payload) {
      state.recentEvents = payload
    },
    SET_RECENT_EVENTS_LOADING (state, payload) {
      state.recentEventsLoading = payload
    },

    SET_GRAPH_QUALITY (state, payload) {
      state.graphQuality = payload
    },
    SET_GRAPH_QUALITY_LOADING (state, payload) {
      state.graphQualityLoading = payload
    },

    SET_DIFY_WORKFLOWS (state, payload) {
      state.difyWorkflows = payload
    },
    SET_DIFY_WORKFLOWS_LOADING (state, payload) {
      state.difyWorkflowsLoading = payload
    },
    SET_SELECTED_WORKFLOW_CODE (state, payload) {
      state.selectedWorkflowCode = payload
    },

    SET_CONTAGION_PATH (state, payload) {
      state.contagionPath = payload
    },
    SET_CONTAGION_PATH_LOADING (state, payload) {
      state.contagionPathLoading = payload
    },

    SET_SMART_MONEY (state, payload) {
      state.smartMoney = payload
    },
    SET_SMART_MONEY_LOADING (state, payload) {
      state.smartMoneyLoading = payload
    },

    SET_EVENT_IMPACT (state, payload) {
      state.eventImpact = payload
    },
    SET_EVENT_IMPACT_LOADING (state, payload) {
      state.eventImpactLoading = payload
    }
  },

  actions: {
    async fetchGraphContext ({ commit }, { market, symbol }) {
      commit('SET_GRAPH_CONTEXT_LOADING', true)
      commit('SET_GRAPH_CONTEXT_ERROR', '')
      try {
        const res = await getGraphContext({ market, symbol })
        if (res.code === 1) {
          commit('SET_GRAPH_CONTEXT', res.data)
        } else {
          commit('SET_GRAPH_CONTEXT_ERROR', res.msg || '查询失败')
          commit('SET_GRAPH_CONTEXT', null)
        }
      } catch (e) {
        commit('SET_GRAPH_CONTEXT_ERROR', e.message)
        commit('SET_GRAPH_CONTEXT', null)
      } finally {
        commit('SET_GRAPH_CONTEXT_LOADING', false)
      }
    },

    async fetchRelatedAssets ({ commit }, { market, symbol }) {
      commit('SET_RELATED_ASSETS_LOADING', true)
      try {
        const res = await getRelatedAssets({ market, symbol })
        if (res.code === 1) {
          commit('SET_RELATED_ASSETS', res.data || [])
        }
      } catch (e) {
        // 静默失败，不影响主流程
      } finally {
        commit('SET_RELATED_ASSETS_LOADING', false)
      }
    },

    async fetchRecentEvents ({ commit }, { symbol, limit = 10 }) {
      commit('SET_RECENT_EVENTS_LOADING', true)
      try {
        const res = await getRecentEvents({ symbol, limit })
        if (res.code === 1) {
          commit('SET_RECENT_EVENTS', res.data || [])
        }
      } catch (e) {
        // 静默失败
      } finally {
        commit('SET_RECENT_EVENTS_LOADING', false)
      }
    },

    async fetchGraphQuality ({ commit }) {
      commit('SET_GRAPH_QUALITY_LOADING', true)
      try {
        const res = await getGraphQuality()
        if (res.code === 1) {
          commit('SET_GRAPH_QUALITY', res.data)
        }
      } catch (e) {
        // 静默失败
      } finally {
        commit('SET_GRAPH_QUALITY_LOADING', false)
      }
    },

    async fetchDifyWorkflows ({ commit }) {
      commit('SET_DIFY_WORKFLOWS_LOADING', true)
      try {
        const res = await getWorkflows()
        if (res.success) {
          commit('SET_DIFY_WORKFLOWS', res.data || [])
        }
      } catch (e) {
        // 静默失败
      } finally {
        commit('SET_DIFY_WORKFLOWS_LOADING', false)
      }
    },

    selectWorkflow ({ commit }, code) {
      commit('SET_SELECTED_WORKFLOW_CODE', code)
    },

    async fetchContagionPath ({ commit }, { from, to, market }) {
      commit('SET_CONTAGION_PATH_LOADING', true)
      try {
        const res = await getContagionPath({ from, to, market })
        if (res.code === 1) {
          commit('SET_CONTAGION_PATH', res.data)
        }
      } catch (e) {
        // 静默失败
      } finally {
        commit('SET_CONTAGION_PATH_LOADING', false)
      }
    },

    async fetchSmartMoney ({ commit }, { symbol, domain }) {
      commit('SET_SMART_MONEY_LOADING', true)
      try {
        const res = await getSmartMoney(symbol, { domain })
        if (res.code === 1) {
          commit('SET_SMART_MONEY', res.data)
        }
      } catch (e) {
        // 静默失败
      } finally {
        commit('SET_SMART_MONEY_LOADING', false)
      }
    },

    async fetchEventImpact ({ commit }, { eventUid, maxDepth = 3 }) {
      commit('SET_EVENT_IMPACT_LOADING', true)
      try {
        const res = await getEventImpact(eventUid, { max_depth: maxDepth })
        if (res.code === 1) {
          commit('SET_EVENT_IMPACT', res.data)
        }
      } catch (e) {
        // 静默失败
      } finally {
        commit('SET_EVENT_IMPACT_LOADING', false)
      }
    }
  }
}

export default graph
