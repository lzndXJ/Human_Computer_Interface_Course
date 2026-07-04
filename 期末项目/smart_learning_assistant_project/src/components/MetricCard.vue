<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  detail: {
    type: String,
    default: '',
  },
  icon: {
    type: [Object, Function],
    default: null,
  },
  tone: {
    type: String,
    default: 'green',
  },
})
</script>

<template>
  <article class="metric-card" :class="`tone-${tone}`">
    <div class="metric-icon">
      <el-icon v-if="icon"><component :is="icon" /></el-icon>
    </div>
    <div>
      <p>{{ title }}</p>
      <strong>{{ value }}</strong>
      <span v-if="detail">{{ detail }}</span>
    </div>
  </article>
</template>

<style scoped>
.metric-card {
  display: flex;
  gap: 14px;
  min-height: 104px;
  padding: 16px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--panel-background);
}

.metric-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  font-size: 1.25rem;
}

.tone-green .metric-icon {
  background: #eaf5f0;
  color: #216450;
}

.tone-blue .metric-icon {
  background: #edf3ff;
  color: #3867d6;
}

.tone-amber .metric-icon {
  background: #fff3de;
  color: #9a5d00;
}

p {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.88rem;
  font-weight: 700;
}

strong {
  display: block;
  margin-top: 5px;
  color: var(--text-strong);
  font-size: 1.65rem;
  font-weight: 800;
  line-height: 1;
}

span {
  display: block;
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 0.9rem;
}
</style>
