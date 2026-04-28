<template>
  <div class="not-found">
    <a-result status="404" title="404" sub-title="Sorry, the page you visited does not exist.">
      <template #extra>
        <a-button type="primary" @click="$router.push('/')">Back Home</a-button>
      </template>
    </a-result>
  </div>
</template>

<style scoped lang="less">
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
</style>
