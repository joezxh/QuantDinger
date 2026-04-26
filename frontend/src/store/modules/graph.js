/**
 * Graph / Dify 状态管理模块
 * 管理图谱上下文、Dify 工作流列表、图谱质量等全局状态
 */
import {
  getGraphContext,
  getRelatedAssets,
  getRecentEvents,
  getGraphQuality
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
    selectedWorkflowCode: ''
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
    }
  }
}

export default graph
