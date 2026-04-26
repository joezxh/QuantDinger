/**
 * v-hasPermi 权限按钮指令
 *
 * 用法：
 *   <a-button v-hasPermi="'system:user:create'">新增用户</a-button>
 *   或
 *   <a-button v-hasPermi="['system:user:create', 'system:user:update']">编辑</a-button>
 *
 * 当用户没有权限时，该元素将从 DOM 中移除。
 */
import Vue from 'vue'

function checkPermission (el, binding, vnode) {
  const permissions = vnode.context.$store?.getters?.permissions || []

  const value = binding.value
  if (!value) {
    // No permission required — keep element
    return
  }

  if (typeof value === 'string') {
    if (!permissions.includes(value)) {
      el.parentNode && el.parentNode.removeChild(el)
    }
  } else if (Array.isArray(value)) {
    // Has ANY of the required permissions
    const hasAny = value.some(p => permissions.includes(p))
    if (!hasAny) {
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}

Vue.directive('hasPermi', {
  inserted (el, binding, vnode) {
    checkPermission(el, binding, vnode)
  },
  update (el, binding, vnode) {
    // Re-check on update
    checkPermission(el, binding, vnode)
  }
})
