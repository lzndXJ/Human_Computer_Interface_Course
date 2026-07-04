<script setup>
import { computed } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  tasks: {
    type: Array,
    default: () => [],
  },
  compact: {
    type: Boolean,
    default: false,
  },
  showActions: {
    type: Boolean,
    default: true,
  },
  emptyText: {
    type: String,
    default: 'No tasks yet.',
  },
})

const emit = defineEmits(['toggle', 'edit', 'delete', 'row-click'])

const visibleTasks = computed(() => {
  return props.compact ? props.tasks.slice(0, 5) : props.tasks
})

function priorityType(priority) {
  const types = {
    High: 'danger',
    Medium: 'warning',
    Low: 'success',
  }

  return types[priority] || 'info'
}

function formatDueDate(dateString) {
  return new Date(`${dateString}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

function taskMetaItems(task) {
  return [
    task.category,
    task.course,
    task.dueDate ? `Due ${formatDueDate(task.dueDate)}` : '',
    task.estimatedMinutes ? `${task.estimatedMinutes} min` : '',
  ].filter(Boolean)
}
</script>

<template>
  <div class="task-list">
    <article
      v-for="task in visibleTasks"
      :key="task.id"
      class="task-row"
      role="button"
      tabindex="0"
      @click="emit('row-click', task)"
      @keydown.enter="emit('row-click', task)"
    >
      <el-checkbox
        :model-value="task.completed"
        size="large"
        @click.stop
        @change="emit('toggle', task.id)"
      />

      <div class="task-main">
        <div class="task-title-line">
          <h3 :class="{ completed: task.completed }">{{ task.title }}</h3>
          <el-tag :type="priorityType(task.priority)" size="small" effect="light">
            {{ task.priority }}
          </el-tag>
        </div>

        <div class="task-meta">
          <span v-for="item in taskMetaItems(task)" :key="item">{{ item }}</span>
        </div>
      </div>

      <div v-if="showActions" class="task-actions">
        <el-tooltip content="Delete task" placement="top">
          <el-button :icon="Delete" circle text type="danger" @click.stop="emit('delete', task.id)" />
        </el-tooltip>
      </div>
    </article>

    <EmptyState v-if="visibleTasks.length === 0" :description="emptyText">
      <slot name="empty-action" />
    </EmptyState>
  </div>
</template>

<style scoped>
.task-list {
  display: grid;
  gap: 10px;
}

.task-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.task-row:hover {
  border-color: #99cabb;
  box-shadow: 0 8px 24px rgba(33, 100, 80, 0.08);
  transform: translateY(-1px);
}

.task-main {
  min-width: 0;
}

.task-title-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

h3 {
  overflow-wrap: anywhere;
  margin: 0;
  color: var(--text-strong);
  font-size: 0.98rem;
  font-weight: 700;
}

h3.completed {
  color: var(--text-muted);
  text-decoration: line-through;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 0.86rem;
}

.task-actions {
  display: flex;
  gap: 4px;
}

@media (max-width: 620px) {
  .task-row {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .task-actions {
    grid-column: 2;
    justify-content: flex-start;
  }
}
</style>
