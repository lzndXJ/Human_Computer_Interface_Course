<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calendar, Checked, Clock, Collection, Compass, TrendCharts, Warning } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import MetricCard from '@/components/MetricCard.vue'
import TaskList from '@/components/TaskList.vue'
import EmptyState from '@/components/EmptyState.vue'
import { getTodayISO, loadLearningData, saveLearningSection } from '@/utils/storage'

const router = useRouter()
const initialData = loadLearningData()

const courses = ref(initialData.courses)
const tasks = ref(initialData.tasks)
const plans = ref(initialData.plans)
const resources = ref(initialData.resources)
const aiSuggestion = ref('')
const aiSuggestionSource = ref('')
const aiLoading = ref(false)

const today = new Date()
const todayName = today.toLocaleDateString('en-US', { weekday: 'long' })
const todayLabel = today.toLocaleDateString('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
})
const todayISO = getTodayISO()

const todaysClasses = computed(() => {
  return courses.value
    .filter((course) => course.day === todayName)
    .sort((a, b) => a.startTime.localeCompare(b.startTime))
})

const todaysPendingTasks = computed(() => {
  return tasks.value
    .filter((task) => !task.completed && task.dueDate === todayISO)
    .sort((a, b) => priorityRank(a.priority) - priorityRank(b.priority))
})

const pendingTasks = computed(() => tasks.value.filter((task) => !task.completed))
const completedTasks = computed(() => tasks.value.filter((task) => task.completed))
const totalEstimatedMinutes = computed(() => {
  return pendingTasks.value.reduce((sum, task) => sum + Number(task.estimatedMinutes || 45), 0)
})

const dueSoonTasks = computed(() => {
  return pendingTasks.value
    .filter((task) => daysUntil(task.dueDate) <= 3)
    .sort((a, b) => daysUntil(a.dueDate) - daysUntil(b.dueDate))
})

const completionRate = computed(() => {
  if (tasks.value.length === 0) return 0
  return Math.round((completedTasks.value.length / tasks.value.length) * 100)
})

const latestPlan = computed(() => plans.value[0] || null)

function priorityRank(priority) {
  return { High: 1, Medium: 2, Low: 3 }[priority] || 4
}

function daysUntil(dateString) {
  if (!dateString) return 999
  const todayStart = new Date()
  const start = new Date(todayStart.getFullYear(), todayStart.getMonth(), todayStart.getDate())
  const target = new Date(`${dateString}T00:00:00`)
  return Math.ceil((target - start) / 86400000)
}

function deadlineText(dateString) {
  const days = daysUntil(dateString)
  if (days < 0) return `${Math.abs(days)} day(s) overdue`
  if (days === 0) return 'Due today'
  return `${days} day(s) left`
}

function buildFallbackSuggestion() {
  if (dueSoonTasks.value.length) {
    const firstTask = dueSoonTasks.value[0]
    return [
      `Start with "${firstTask.title}" because it is ${deadlineText(firstTask.dueDate).toLowerCase()}.`,
      `Use a 45-minute focused block, then review related resources for ${firstTask.course || 'this topic'}.`,
      `After that, update the task status so the dashboard progress stays accurate.`,
    ].join(' ')
  }

  if (pendingTasks.value.length) {
    const highPriorityTask = [...pendingTasks.value].sort(
      (a, b) => priorityRank(a.priority) - priorityRank(b.priority),
    )[0]

    return [
      `Your study queue is stable today. Pick "${highPriorityTask.title}" as the next task.`,
      `Break it into one small outcome and spend about ${highPriorityTask.estimatedMinutes || 45} minutes on it.`,
      'Save any useful material in Resources so it remains connected to your course work.',
    ].join(' ')
  }

  return 'No urgent work is waiting. Use the Planner to prepare the next study session or add upcoming course tasks.'
}

function buildAiPayload() {
  return {
    today: todayLabel,
    metrics: {
      classesToday: todaysClasses.value.length,
      pendingTasks: pendingTasks.value.length,
      completionRate: completionRate.value,
      estimatedPendingMinutes: totalEstimatedMinutes.value,
      savedResources: resources.value.length,
    },
    urgentTasks: dueSoonTasks.value.slice(0, 5).map((task) => ({
      title: task.title,
      course: task.course || 'No course linked',
      priority: task.priority,
      dueDate: task.dueDate,
      deadline: deadlineText(task.dueDate),
      estimatedMinutes: task.estimatedMinutes || 45,
    })),
    resources: resources.value.slice(0, 5).map((resource) => ({
      title: resource.title,
      course: resource.course || 'No course linked',
      type: resource.type,
    })),
  }
}

async function generateAiSuggestion() {
  aiLoading.value = true

  try {
    const response = await fetch('/api/study-suggestion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildAiPayload()),
    })

    if (!response.ok) throw new Error('AI service is unavailable.')

    const data = await response.json()
    aiSuggestion.value = data.suggestion || buildFallbackSuggestion()
    aiSuggestionSource.value = data.source || 'AI'
    ElMessage.success('Study suggestion generated.')
  } catch (error) {
    aiSuggestion.value = buildFallbackSuggestion()
    aiSuggestionSource.value = 'Local fallback'
    ElMessage.info('Generated with local study rules.')
  } finally {
    aiLoading.value = false
  }
}

function toggleTask(taskId) {
  tasks.value = tasks.value.map((task) =>
    task.id === taskId ? { ...task, completed: !task.completed } : task,
  )
  saveLearningSection('tasks', tasks.value)
}
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="Today"
      title="Your learning start point"
      :description="`Plan the next step from your classes, tasks, and study goals for ${todayLabel}.`"
    >
      <template #actions>
        <el-button type="primary" :icon="Checked" @click="router.push('/tasks')">Manage tasks</el-button>
        <el-button :icon="Compass" @click="router.push('/planner')">Open planner</el-button>
      </template>
    </PageHeader>

    <div class="responsive-grid">
      <MetricCard
        title="Classes today"
        :value="todaysClasses.length"
        :detail="todaysClasses.length ? 'Follow your schedule first' : 'No scheduled class blocks'"
        :icon="Calendar"
        tone="green"
      />
      <MetricCard
        title="Pending tasks"
        :value="pendingTasks.length"
        detail="Across all courses"
        :icon="Checked"
        tone="blue"
      />
      <MetricCard
        title="Completed"
        :value="`${completionRate}%`"
        detail="Current task progress"
        :icon="TrendCharts"
        tone="amber"
      />
      <MetricCard
        title="Study time"
        :value="`${Math.round(totalEstimatedMinutes / 60)}h`"
        detail="Estimated pending study time"
        :icon="Clock"
        tone="green"
      />
      <MetricCard
        title="Resources"
        :value="resources.length"
        detail="Saved course materials"
        :icon="Collection"
        tone="blue"
      />
    </div>

    <div class="dashboard-grid">
      <section class="panel reminder-panel">
        <div class="section-heading">
          <h2 class="section-title">Deadline Reminders</h2>
          <el-tag :type="dueSoonTasks.length ? 'warning' : 'success'" effect="plain">
            <el-icon><Warning /></el-icon>
            {{ dueSoonTasks.length }} urgent
          </el-tag>
        </div>
        <div v-if="dueSoonTasks.length" class="reminder-list">
          <article
            v-for="task in dueSoonTasks.slice(0, 4)"
            :key="task.id"
            class="reminder-item"
            role="button"
            tabindex="0"
            @click="router.push('/tasks')"
            @keydown.enter="router.push('/tasks')"
          >
            <div>
              <strong>{{ task.title }}</strong>
              <p>{{ task.course || 'No course linked' }}</p>
            </div>
            <el-tag :type="daysUntil(task.dueDate) <= 0 ? 'danger' : 'warning'" size="small">
              {{ deadlineText(task.dueDate) }}
            </el-tag>
          </article>
        </div>
        <EmptyState v-else description="No urgent deadline within three days." />
      </section>

      <section class="panel ai-panel">
        <div class="section-heading">
          <h2 class="section-title">AI Study Suggestion</h2>
          <el-tag effect="plain">{{ aiSuggestionSource || 'Ready' }}</el-tag>
        </div>
        <p class="ai-copy">
          {{ aiSuggestion || 'Generate a focused study suggestion from current tasks, deadlines, and saved resources.' }}
        </p>
        <el-button type="primary" :loading="aiLoading" @click="generateAiSuggestion">
          Generate suggestion
        </el-button>
      </section>

      <section class="panel">
        <h2 class="section-title">Today's Classes</h2>
        <div v-if="todaysClasses.length" class="class-list">
          <article
            v-for="course in todaysClasses"
            :key="course.id"
            class="class-item"
            role="button"
            tabindex="0"
            @click="router.push('/schedule')"
            @keydown.enter="router.push('/schedule')"
          >
            <span class="course-color" :style="{ backgroundColor: course.color }"></span>
            <div>
              <h3>{{ course.name }}</h3>
              <p>{{ course.startTime }} - {{ course.endTime }} · {{ course.room }}</p>
            </div>
          </article>
        </div>
        <EmptyState v-else description="No classes are scheduled for today." />
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2 class="section-title">Today's Pending Tasks</h2>
          <el-button text type="primary" @click="router.push('/tasks')">View all</el-button>
        </div>
        <TaskList
          :tasks="todaysPendingTasks"
          compact
          :show-actions="false"
          empty-text="No pending tasks due today."
          @toggle="toggleTask"
          @row-click="router.push('/tasks')"
        />
      </section>

      <section class="panel next-step-panel">
        <div>
          <h2 class="section-title">Suggested Next Step</h2>
          <p v-if="todaysPendingTasks.length">
            Start with <strong>{{ todaysPendingTasks[0].title }}</strong> because it is due today.
          </p>
          <p v-else-if="todaysClasses.length">
            Review materials for <strong>{{ todaysClasses[0].name }}</strong> before class.
          </p>
          <p v-else>
            Use the guided planner to turn free time into a simple study plan.
          </p>
        </div>
        <el-button type="primary" :icon="Clock" @click="router.push('/planner')">
          Plan study time
        </el-button>
      </section>

      <section class="panel">
        <h2 class="section-title">Latest Study Plan</h2>
        <div
          v-if="latestPlan"
          class="latest-plan"
          role="button"
          tabindex="0"
          @click="router.push('/planner')"
          @keydown.enter="router.push('/planner')"
        >
          <strong>{{ latestPlan.subject }}</strong>
          <p>{{ latestPlan.time }} · {{ latestPlan.goal }}</p>
        </div>
        <EmptyState v-else description="No study plan has been generated yet." />
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 16px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.class-list {
  display: grid;
  gap: 10px;
}

.reminder-list {
  display: grid;
  gap: 12px;
}

.reminder-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.reminder-item strong {
  color: var(--text-strong);
  font-weight: 800;
}

.reminder-item p {
  color: var(--text-muted);
}

.reminder-item p {
  margin: 2px 0 0;
}

.reminder-item {
  padding: 12px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.reminder-item:hover,
.class-item:hover,
.latest-plan:hover {
  border-color: #99cabb;
  box-shadow: 0 8px 24px rgba(33, 100, 80, 0.08);
  transform: translateY(-1px);
}

.ai-copy {
  margin: 0 0 16px;
  color: var(--text-body);
  line-height: 1.7;
}

.class-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  align-items: center;
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

.course-color {
  width: 8px;
  height: 42px;
  border-radius: 8px;
}

h3,
.latest-plan strong {
  display: block;
  margin: 0;
  color: var(--text-strong);
  font-weight: 700;
}

.latest-plan {
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

.class-item p,
.latest-plan p,
.next-step-panel p {
  margin: 4px 0 0;
  color: var(--text-muted);
}

.next-step-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

@media (max-width: 980px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .next-step-panel {
    display: grid;
    justify-items: start;
  }
}
</style>
