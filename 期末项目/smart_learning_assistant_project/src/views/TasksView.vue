<script setup>
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Check, Delete, Plus } from '@element-plus/icons-vue'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import TaskEditorDialog from '@/components/TaskEditorDialog.vue'
import { getTodayISO, loadLearningData, saveLearningSection } from '@/utils/storage'

const initialData = loadLearningData()
const courses = ref(initialData.courses)
const tasks = ref(initialData.tasks)

const dialogVisible = ref(false)
const editingTask = ref(null)
const statusFilter = ref('all')
const priorityFilter = ref('all')
const courseFilter = ref('all')

const priorityOrder = {
  High: 1,
  Medium: 2,
  Low: 3,
}

const todayISO = getTodayISO()
const tomorrowISO = addDaysISO(1)

const taskStats = computed(() => {
  const total = tasks.value.length
  const completed = tasks.value.filter((task) => task.completed).length
  const pending = total - completed

  return {
    total,
    completed,
    pending,
  }
})

const filteredTasks = computed(() => {
  return [...tasks.value]
    .filter((task) => {
      if (statusFilter.value === 'pending') return !task.completed
      if (statusFilter.value === 'completed') return task.completed
      return true
    })
    .filter((task) => priorityFilter.value === 'all' || task.priority === priorityFilter.value)
    .filter((task) => courseFilter.value === 'all' || task.course === courseFilter.value)
    .sort((a, b) => {
      if (a.completed !== b.completed) return a.completed ? 1 : -1
      if (a.dueDate !== b.dueDate) return (a.dueDate || '').localeCompare(b.dueDate || '')
      return (priorityOrder[a.priority] || 4) - (priorityOrder[b.priority] || 4)
    })
})

const completionRate = computed(() => {
  if (taskStats.value.total === 0) return 0
  return Math.round((taskStats.value.completed / taskStats.value.total) * 100)
})

const groupedTasks = computed(() => {
  const groups = new Map()

  filteredTasks.value.forEach((task) => {
    const groupKey = task.dueDate || 'no-date'
    if (!groups.has(groupKey)) {
      groups.set(groupKey, {
        key: groupKey,
        ...formatGroupLabel(groupKey),
        tasks: [],
      })
    }

    groups.get(groupKey).tasks.push(task)
  })

  return [...groups.values()]
    .map((group) => ({
      ...group,
      tasks: group.tasks.sort(sortTasksWithinDay),
    }))
    .sort((a, b) => sortGroups(a.key, b.key))
})

const hasVisibleTasks = computed(() => groupedTasks.value.some((group) => group.tasks.length))

function openAddDialog() {
  editingTask.value = null
  dialogVisible.value = true
}

function openEditDialog(task) {
  editingTask.value = { ...task }
  dialogVisible.value = true
}

function saveTask(taskData) {
  if (taskData.id) {
    tasks.value = tasks.value.map((task) => (task.id === taskData.id ? taskData : task))
    ElMessage.success('Task updated.')
  } else {
    tasks.value = [
      {
        ...taskData,
        id: `task-${Date.now()}`,
        completed: false,
      },
      ...tasks.value,
    ]
    ElMessage.success('Task added.')
  }

  saveLearningSection('tasks', tasks.value)
}

function toggleTask(taskId) {
  tasks.value = tasks.value.map((task) =>
    task.id === taskId ? { ...task, completed: !task.completed } : task,
  )
  saveLearningSection('tasks', tasks.value)
}

function deleteTask(taskId) {
  ElMessageBox.confirm('This task will be removed from your local list.', 'Delete task?', {
    confirmButtonText: 'Delete',
    cancelButtonText: 'Cancel',
    type: 'warning',
  })
    .then(() => {
      tasks.value = tasks.value.filter((task) => task.id !== taskId)
      saveLearningSection('tasks', tasks.value)
      ElMessage.success('Task deleted.')
    })
    .catch(() => {})
}

function addDaysISO(daysToAdd) {
  const date = new Date()
  date.setDate(date.getDate() + daysToAdd)
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  return date.toISOString().slice(0, 10)
}

function dateFromISO(dateString) {
  return new Date(`${dateString}T00:00:00`)
}

function formatGroupLabel(dateString) {
  if (dateString === 'no-date') {
    return {
      label: 'No date',
      detail: 'Unscheduled',
      tone: 'neutral',
    }
  }

  const date = dateFromISO(dateString)
  const weekday = date.toLocaleDateString('en-US', { weekday: 'short' })

  if (dateString === todayISO) {
    return {
      label: 'Today',
      detail: weekday,
      tone: 'today',
    }
  }

  if (dateString === tomorrowISO) {
    return {
      label: 'Tomorrow',
      detail: weekday,
      tone: 'upcoming',
    }
  }

  if (dateString < todayISO) {
    return {
      label: 'Overdue',
      detail: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' }),
      tone: 'overdue',
    }
  }

  return {
    label: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    detail: weekday,
    tone: 'upcoming',
  }
}

function sortGroups(firstKey, secondKey) {
  if (firstKey === 'no-date') return 1
  if (secondKey === 'no-date') return -1
  return firstKey.localeCompare(secondKey)
}

function sortTasksWithinDay(firstTask, secondTask) {
  if (firstTask.completed !== secondTask.completed) return firstTask.completed ? 1 : -1
  return (priorityOrder[firstTask.priority] || 4) - (priorityOrder[secondTask.priority] || 4)
}

function priorityColor(priority) {
  const colors = {
    High: '#f56c6c',
    Medium: '#e6a23c',
    Low: '#14b8a6',
  }

  return colors[priority] || '#909399'
}

function priorityText(priority) {
  return `${priority || 'Normal'} priority`
}

function taskMeta(task) {
  return [task.category, task.course, task.estimatedMinutes ? `${task.estimatedMinutes} min` : '']
    .filter(Boolean)
    .join(' · ')
}
</script>

<template>
  <div class="page-stack tasks-page">
    <PageHeader
      eyebrow="Todo list"
      title="Tasks"
      description="Review study work by date, complete items quickly, and keep upcoming tasks visible."
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openAddDialog">Add task</el-button>
      </template>
    </PageHeader>

    <section class="todo-shell">
      <div class="task-toolbar">
        <div class="task-progress">
          <div class="progress-title">
            <el-icon><Calendar /></el-icon>
            <span>{{ taskStats.pending }} pending</span>
            <strong>{{ completionRate }}%</strong>
          </div>
          <el-progress :percentage="completionRate" :stroke-width="10" />
        </div>

        <div class="filters">
          <el-radio-group v-model="statusFilter">
            <el-radio-button label="all">All</el-radio-button>
            <el-radio-button label="pending">Pending</el-radio-button>
            <el-radio-button label="completed">Completed</el-radio-button>
          </el-radio-group>

          <el-select v-model="priorityFilter" class="priority-select" aria-label="Priority filter">
            <el-option label="All priorities" value="all" />
            <el-option label="High" value="High" />
            <el-option label="Medium" value="Medium" />
            <el-option label="Low" value="Low" />
          </el-select>

          <el-select v-model="courseFilter" class="course-select" aria-label="Course filter">
            <el-option label="All courses" value="all" />
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.name"
            />
          </el-select>
        </div>
      </div>

      <div v-if="hasVisibleTasks" class="date-task-list">
        <section
          v-for="group in groupedTasks"
          :key="group.key"
          class="date-section"
          :class="`tone-${group.tone}`"
        >
          <header class="date-divider">
            <strong>{{ group.label }}</strong>
            <span>{{ group.detail }}</span>
          </header>

          <article
            v-for="task in group.tasks"
            :key="task.id"
            class="todo-item"
            :class="{ completed: task.completed }"
            :style="{ borderLeftColor: priorityColor(task.priority) }"
            role="button"
            tabindex="0"
            @click="openEditDialog(task)"
            @keydown.enter="openEditDialog(task)"
          >
            <button
              type="button"
              class="check-button"
              :class="{ checked: task.completed }"
              :style="{ borderColor: priorityColor(task.priority), backgroundColor: task.completed ? priorityColor(task.priority) : '#ffffff' }"
              :aria-label="task.completed ? 'Mark task as pending' : 'Mark task as completed'"
              @click.stop="toggleTask(task.id)"
            >
              <el-icon v-if="task.completed"><Check /></el-icon>
            </button>

            <div class="todo-content">
              <div class="todo-title-row">
                <h2>{{ task.title }}</h2>
                <span class="priority-chip" :style="{ color: priorityColor(task.priority) }">
                  {{ priorityText(task.priority) }}
                </span>
              </div>
              <p v-if="taskMeta(task)">{{ taskMeta(task) }}</p>
              <p v-if="task.notes" class="task-notes">{{ task.notes }}</p>
            </div>

            <div class="todo-actions">
              <el-tooltip content="Delete task" placement="top">
                <el-button
                  :icon="Delete"
                  circle
                  text
                  type="danger"
                  size="small"
                  @click.stop="deleteTask(task.id)"
                />
              </el-tooltip>
            </div>
          </article>
        </section>
      </div>

      <EmptyState v-else description="No tasks match the current filters.">
        <template #default>
          <el-button type="primary" :icon="Plus" @click="openAddDialog">Add task</el-button>
        </template>
      </EmptyState>
    </section>

    <TaskEditorDialog
      v-model="dialogVisible"
      :task="editingTask"
      :courses="courses"
      @save="saveTask"
    />
  </div>
</template>

<style scoped>
.tasks-page {
  position: relative;
}

.todo-shell {
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #ffffff;
}

.task-toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) auto;
  gap: 16px;
  align-items: end;
  padding: 18px 20px;
  border-bottom: 1px solid var(--app-border);
  background: #ffffff;
}

.task-progress {
  display: grid;
  gap: 10px;
}

.progress-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f8f87;
  font-weight: 800;
}

.progress-title strong {
  color: var(--text-muted);
  font-size: 0.9rem;
  font-weight: 700;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.priority-select,
.course-select {
  width: 160px;
}

.date-task-list {
  display: grid;
}

.date-section {
  display: grid;
}

.date-divider {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 20px;
  background: #e5f6f4;
  color: #0f8f87;
  font-size: 0.9rem;
}

.date-divider strong {
  font-weight: 800;
}

.date-divider span {
  font-size: 0.82rem;
  font-weight: 700;
}

.tone-overdue .date-divider {
  background: #fff1f0;
  color: #cf4b45;
}

.tone-upcoming .date-divider {
  background: #eef5ff;
  color: #3867d6;
}

.tone-neutral .date-divider {
  background: #f2f4f5;
  color: var(--text-muted);
}

.todo-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 14px;
  align-items: start;
  min-height: 76px;
  padding: 16px 18px;
  border-bottom: 1px solid #edf0f2;
  border-left: 4px solid transparent;
  background: #ffffff;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    box-shadow 0.2s ease;
}

.todo-item:hover {
  background: #fbfffd;
  box-shadow: inset 0 0 0 1px #cfe6de;
}

.todo-item.completed {
  background: #fbfcfc;
}

.check-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  margin-top: 3px;
  border: 2px solid;
  border-radius: 4px;
  color: #ffffff;
  cursor: pointer;
}

.todo-content {
  min-width: 0;
}

.todo-title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.todo-title-row h2 {
  margin: 0;
  color: var(--text-strong);
  font-size: 1rem;
  font-weight: 800;
  line-height: 1.4;
  overflow-wrap: break-word;
  word-break: normal;
}

.completed .todo-title-row h2,
.completed .todo-content p {
  color: #9aa5a2;
  text-decoration: line-through;
}

.priority-chip {
  flex: 0 0 auto;
  font-size: 0.82rem;
  font-weight: 800;
}

.todo-content p {
  margin: 5px 0 0;
  color: var(--text-muted);
}

.task-notes {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  font-size: 0.9rem;
}

.todo-actions {
  display: flex;
  gap: 2px;
}

@media (max-width: 820px) {
  .task-toolbar {
    grid-template-columns: 1fr;
  }

  .filters {
    justify-content: flex-start;
  }

  .todo-item {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .todo-actions {
    grid-column: 2;
  }

  .todo-title-row {
    display: grid;
    gap: 4px;
  }

}
</style>
