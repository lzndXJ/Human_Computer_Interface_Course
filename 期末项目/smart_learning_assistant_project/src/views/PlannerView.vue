<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Check, Delete, Microphone, Plus, Refresh, Right, VideoPause } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { getTodayISO, loadLearningData, saveLearningSection } from '@/utils/storage'

const initialData = loadLearningData()
const plans = ref(initialData.plans)
const tasks = ref(initialData.tasks)
const courses = ref(initialData.courses)

const steps = [
  {
    key: 'subject',
    title: 'Subject',
    question: 'What subject do you want to study?',
    placeholder: 'e.g., Human-Computer Interaction',
  },
  {
    key: 'time',
    title: 'Time',
    question: 'How much time do you have today?',
    placeholder: 'e.g., 90 minutes',
  },
  {
    key: 'goal',
    title: 'Goal',
    question: 'What is your goal?',
    placeholder: 'e.g., Finish the planner prototype flow',
  },
]

const currentStepIndex = ref(0)
const answers = reactive({
  subject: '',
  time: '',
  goal: '',
})
const generatedPlan = ref(null)
const isListening = ref(false)
const languageMode = ref('en-US')
const isGeneratingPlan = ref(false)
let recognition = null

const currentStep = computed(() => steps[currentStepIndex.value])
const voiceSupported = computed(() => {
  return typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)
})
const activeVoiceLanguageLabel = computed(() => {
  return languageMode.value === 'zh-CN' ? 'Chinese' : 'English'
})

async function nextStep() {
  const key = currentStep.value.key

  if (!answers[key].trim()) {
    ElMessage.warning('Please answer this step first.')
    return
  }

  if (currentStepIndex.value < steps.length - 1) {
    currentStepIndex.value += 1
  } else {
    await generatePlan()
  }
}

function previousStep() {
  if (currentStepIndex.value > 0) currentStepIndex.value -= 1
}

function startVoiceInput() {
  if (!voiceSupported.value) {
    ElMessage.warning('Voice input is not supported in this browser.')
    return
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.lang = languageMode.value
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  recognition.onstart = () => {
    isListening.value = true
  }

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript
    answers[currentStep.value.key] = transcript
  }

  recognition.onerror = () => {
    ElMessage.warning('Voice input stopped. You can continue by typing.')
  }

  recognition.onend = () => {
    isListening.value = false
  }

  recognition.start()
}

function stopVoiceInput() {
  if (recognition) recognition.stop()
  isListening.value = false
}

async function generatePlan() {
  isGeneratingPlan.value = true

  try {
    const planResult = await generatePlanWithAi()

    if (!planResult.valid) {
      ElMessage.warning(planResult.reason || 'Please enter a realistic subject, time, and study goal.')
      return
    }

    createPlan(planResult)
  } finally {
    isGeneratingPlan.value = false
  }
}

function createPlan(planResult) {
  const minutes = planResult.minutes
  const plan = {
    id: `plan-${Date.now()}`,
    createdAt: new Date().toISOString(),
    subject: planResult.cleanedSubject,
    time: answers.time.trim(),
    goal: planResult.cleanedGoal,
    summary: planResult.summary || '',
    source: planResult.source || 'Local rules',
    steps: planResult.steps?.length ? planResult.steps : buildPlanSteps(minutes),
  }

  generatedPlan.value = plan
  plans.value = [plan, ...plans.value].slice(0, 5)
  saveLearningSection('plans', plans.value)
  ElMessage.success('Study plan saved locally.')
}

async function generatePlanWithAi() {
  try {
    const response = await fetch('/api/generate-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: answers.subject.trim(),
        time: answers.time.trim(),
        goal: answers.goal.trim(),
      }),
    })

    if (!response.ok) throw new Error('AI plan generation is unavailable.')

    const data = await response.json()
    return {
      valid: Boolean(data.valid),
      reason: data.reason,
      cleanedSubject: data.cleanedSubject || answers.subject.trim(),
      cleanedGoal: data.cleanedGoal || answers.goal.trim(),
      minutes: Number(data.minutes || extractMinutes(answers.time)),
      summary: data.summary || '',
      steps: normalizePlanSteps(data.steps),
      source: data.source || 'AI',
    }
  } catch (error) {
    const localResult = validatePlanInputLocally()
    if (!localResult.valid) return localResult

    ElMessage.info('AI generation unavailable. Used local study rules.')
    return {
      ...localResult,
      summary: 'A simple local plan was generated from your subject, time, and goal.',
      steps: buildPlanSteps(localResult.minutes),
      source: 'Local rules',
    }
  }
}

function validatePlanInputLocally() {
  const subject = answers.subject.trim()
  const goal = answers.goal.trim()
  const minutes = extractMinutes(answers.time)

  if (!looksMeaningful(subject, 2)) {
    return {
      valid: false,
      reason: 'Please enter a recognizable study subject.',
    }
  }

  if (!Number.isFinite(minutes) || minutes < 15 || minutes > 360) {
    return {
      valid: false,
      reason: 'Please enter a realistic study time between 15 and 360 minutes.',
    }
  }

  if (!looksMeaningful(goal, 4)) {
    return {
      valid: false,
      reason: 'Please enter a concrete learning goal.',
    }
  }

  return {
    valid: true,
    reason: '',
    cleanedSubject: subject,
    cleanedGoal: goal,
    minutes,
  }
}

function normalizePlanSteps(steps) {
  if (!Array.isArray(steps)) return []

  return steps
    .map((step) => ({
      label: String(step.label || '').trim(),
      minutes: Number(step.minutes || 0),
      detail: String(step.detail || '').trim(),
    }))
    .filter((step) => step.label && step.minutes > 0 && step.detail)
    .slice(0, 5)
}

function looksMeaningful(text, minLength) {
  const normalized = text.replace(/\s+/g, '')
  const hasLetterOrChinese = /[a-zA-Z\u4e00-\u9fff]/.test(normalized)
  const uniqueChars = new Set(normalized).size
  const repeatedNoise = /(.)\1{3,}/.test(normalized)

  return normalized.length >= minLength && hasLetterOrChinese && uniqueChars >= 2 && !repeatedNoise
}

function addPlanToTasks(plan) {
  if (!plan) return

  const latestData = loadLearningData()
  tasks.value = latestData.tasks

  if (isPlanTaskAdded(plan)) {
    ElMessage.info('This plan is already in Tasks.')
    return
  }

  const task = createTaskFromPlan(plan)
  tasks.value = [task, ...tasks.value]
  saveLearningSection('tasks', tasks.value)

  plans.value = plans.value.map((savedPlan) =>
    savedPlan.id === plan.id ? { ...savedPlan, taskId: task.id } : savedPlan,
  )
  saveLearningSection('plans', plans.value)

  if (generatedPlan.value?.id === plan.id) {
    generatedPlan.value = { ...generatedPlan.value, taskId: task.id }
  }

  ElMessage.success('Added to Tasks.')
}

function deletePlan(plan) {
  if (!plan) return

  const latestData = loadLearningData()
  const linkedTaskExists = plan.taskId && latestData.tasks.some((task) => task.id === plan.taskId)
  const message = linkedTaskExists
    ? 'This plan and its linked task will be removed.'
    : 'This plan will be removed from Recent Plans.'

  ElMessageBox.confirm(message, 'Delete plan?', {
    confirmButtonText: 'Delete',
    cancelButtonText: 'Cancel',
    type: 'warning',
  })
    .then(() => {
      const currentData = loadLearningData()

      plans.value = currentData.plans.filter((savedPlan) => savedPlan.id !== plan.id)
      saveLearningSection('plans', plans.value)

      if (plan.taskId) {
        tasks.value = currentData.tasks.filter((task) => task.id !== plan.taskId)
        saveLearningSection('tasks', tasks.value)
      } else {
        tasks.value = currentData.tasks
      }

      if (generatedPlan.value?.id === plan.id) {
        resetPlanner()
      }

      ElMessage.success(linkedTaskExists ? 'Plan and linked task deleted.' : 'Plan deleted.')
    })
    .catch(() => {})
}

function createTaskFromPlan(plan) {
  const matchedCourse = courses.value.find((course) => {
    return course.name.toLowerCase() === plan.subject.toLowerCase()
  })

  return {
    id: `task-${Date.now()}`,
    title: plan.goal || `Study ${plan.subject}`,
    course: matchedCourse ? matchedCourse.name : '',
    category: 'Study Plan',
    priority: 'Medium',
    dueDate: getTodayISO(),
    completed: false,
    notes: buildPlanNotes(plan),
  }
}

function buildPlanNotes(plan) {
  const summary = plan.summary ? `Summary: ${plan.summary}\n` : ''
  const planSteps = plan.steps
    .map((step) => `${step.label}: ${step.minutes} min - ${step.detail}`)
    .join('\n')

  return `Subject: ${plan.subject}\nTime: ${plan.time}\nGoal: ${plan.goal}\n${summary}\n${planSteps}`
}

function isPlanTaskAdded(plan) {
  if (!plan?.taskId) return false
  return tasks.value.some((task) => task.id === plan.taskId)
}

function extractMinutes(timeText) {
  const number = Number((timeText.match(/\d+/) || [NaN])[0])
  return Number.isFinite(number) && number > 0 ? number : NaN
}

function buildPlanSteps(minutes) {
  if (minutes >= 90) {
    return [
      { label: 'Set up', minutes: 10, detail: 'Open materials and define the exact output.' },
      { label: 'Deep work', minutes: Math.round(minutes * 0.55), detail: 'Work on the most important part of the goal.' },
      { label: 'Practice', minutes: Math.round(minutes * 0.25), detail: 'Apply the idea with notes, exercises, or prototype edits.' },
      { label: 'Review', minutes: 10, detail: 'Write the next action before stopping.' },
    ]
  }

  return [
    { label: 'Focus', minutes: Math.max(20, Math.round(minutes * 0.65)), detail: 'Work on one clear part of the goal.' },
    { label: 'Check', minutes: Math.max(8, Math.round(minutes * 0.2)), detail: 'Compare progress with the target outcome.' },
    { label: 'Wrap up', minutes: Math.max(5, Math.round(minutes * 0.15)), detail: 'Record what to continue later.' },
  ]
}

function resetPlanner() {
  answers.subject = ''
  answers.time = ''
  answers.goal = ''
  currentStepIndex.value = 0
  generatedPlan.value = null
}

function openPlan(plan) {
  generatedPlan.value = plan
}

function formatPlanDate(dateString) {
  return new Date(dateString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onBeforeUnmount(() => {
  stopVoiceInput()
})
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="Guided planning"
      title="Study planner"
      description="Move through three focused prompts, using typing or voice input, and finish with a simple plan."
    />

    <div class="planner-grid">
      <section class="panel planner-panel">
        <el-steps :active="currentStepIndex" finish-status="success" align-center>
          <el-step v-for="step in steps" :key="step.key" :title="step.title" />
        </el-steps>

        <div v-if="!generatedPlan" class="step-card">
          <p class="step-count">Step {{ currentStepIndex + 1 }} of {{ steps.length }}</p>
          <h2>{{ currentStep.question }}</h2>

          <el-input
            v-model="answers[currentStep.key]"
            type="textarea"
            :rows="4"
            :placeholder="currentStep.placeholder"
          />

          <div class="voice-row">
            <el-radio-group v-model="languageMode" size="small" :disabled="isListening">
              <el-radio-button label="en-US">English</el-radio-button>
              <el-radio-button label="zh-CN">Chinese</el-radio-button>
            </el-radio-group>

            <el-button
              v-if="!isListening"
              :icon="Microphone"
              :disabled="!voiceSupported"
              @click="startVoiceInput"
            >
              Voice input
            </el-button>
            <el-button v-else type="warning" :icon="VideoPause" @click="stopVoiceInput">
              Stop listening
            </el-button>
            <span class="muted-text">
              {{ voiceSupported ? `Voice language: ${activeVoiceLanguageLabel}` : 'Voice input is unavailable here.' }}
            </span>
          </div>

          <div class="planner-actions">
            <el-button :icon="Back" :disabled="currentStepIndex === 0" @click="previousStep">
              Back
            </el-button>
            <el-button
              type="primary"
              :icon="currentStepIndex === steps.length - 1 ? Check : Right"
              :loading="isGeneratingPlan"
              @click="nextStep"
            >
              {{ currentStepIndex === steps.length - 1 ? 'Generate plan' : 'Next' }}
            </el-button>
          </div>
        </div>

        <div v-else class="plan-result">
          <el-result icon="success" title="Today's study plan is ready" />
          <div class="plan-summary">
            <h2>{{ generatedPlan.subject }}</h2>
            <p>{{ generatedPlan.time }} - {{ generatedPlan.goal }}</p>
            <p v-if="generatedPlan.summary" class="ai-summary">{{ generatedPlan.summary }}</p>
            <el-tag v-if="generatedPlan.source" effect="plain" size="small">
              {{ generatedPlan.source }}
            </el-tag>
            <ol>
              <li v-for="item in generatedPlan.steps" :key="item.label">
                <strong>{{ item.label }} - {{ item.minutes }} min</strong>
                <span>{{ item.detail }}</span>
              </li>
            </ol>
          </div>
          <div class="result-actions">
            <el-button
              type="primary"
              :icon="Plus"
              :disabled="isPlanTaskAdded(generatedPlan)"
              @click="addPlanToTasks(generatedPlan)"
            >
              {{ isPlanTaskAdded(generatedPlan) ? 'Added to Tasks' : 'Add to Tasks' }}
            </el-button>
            <el-button :icon="Refresh" @click="resetPlanner">Plan another session</el-button>
            <el-button type="danger" plain :icon="Delete" @click="deletePlan(generatedPlan)">
              Delete plan
            </el-button>
          </div>
        </div>
      </section>

      <aside class="panel">
        <h2 class="section-title">Recent Plans</h2>
        <div v-if="plans.length" class="recent-plans">
          <article
            v-for="plan in plans"
            :key="plan.id"
            class="recent-plan"
            role="button"
            tabindex="0"
            @click="openPlan(plan)"
            @keydown.enter="openPlan(plan)"
          >
            <strong>{{ plan.subject }}</strong>
            <p>{{ plan.goal }}</p>
            <span>{{ formatPlanDate(plan.createdAt) }}</span>
            <div class="recent-plan-actions">
              <el-button
                size="small"
                :icon="Plus"
                :disabled="isPlanTaskAdded(plan)"
                @click.stop="addPlanToTasks(plan)"
              >
                {{ isPlanTaskAdded(plan) ? 'In Tasks' : 'Add task' }}
              </el-button>
              <el-button size="small" type="danger" plain :icon="Delete" @click.stop="deletePlan(plan)">
                Delete
              </el-button>
            </div>
          </article>
        </div>
        <EmptyState v-else description="Generated plans will appear here." />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.planner-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: start;
}

.planner-panel {
  display: grid;
  gap: 24px;
}

.step-card,
.plan-result {
  display: grid;
  gap: 18px;
}

.step-count {
  margin: 0;
  color: var(--accent-green);
  font-weight: 800;
}

h2 {
  margin: 0;
  color: var(--text-strong);
  font-size: 1.35rem;
  font-weight: 800;
}

.voice-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.planner-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.plan-summary {
  padding: 16px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #ffffff;
}

.plan-summary p,
.recent-plan p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.plan-summary .ai-summary {
  color: var(--text-body);
  line-height: 1.7;
}

ol {
  display: grid;
  gap: 10px;
  margin: 16px 0 0;
  padding-left: 20px;
}

li strong,
.recent-plan strong {
  display: block;
  color: var(--text-strong);
  font-weight: 800;
}

li span,
.recent-plan span {
  display: block;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.recent-plans {
  display: grid;
  gap: 10px;
}

.recent-plan {
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

.recent-plan:hover {
  border-color: #99cabb;
  box-shadow: 0 8px 24px rgba(33, 100, 80, 0.08);
  transform: translateY(-1px);
}

.recent-plan-actions {
  margin-top: 12px;
}

@media (max-width: 980px) {
  .planner-grid {
    grid-template-columns: 1fr;
  }
}
</style>
