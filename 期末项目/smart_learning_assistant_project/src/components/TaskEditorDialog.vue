<script setup>
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  task: {
    type: Object,
    default: null,
  },
  courses: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue', 'save'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const form = reactive(createEmptyTask())

function createEmptyTask() {
  return {
    id: '',
    title: '',
    course: '',
    category: '',
    priority: 'Medium',
    dueDate: '',
    completed: false,
    estimatedMinutes: null,
    notes: '',
  }
}

function resetForm(task) {
  Object.assign(form, createEmptyTask(), task || {})
}

watch(
  () => props.modelValue,
  (isVisible) => {
    if (isVisible) resetForm(props.task)
  },
)

watch(
  () => props.task,
  (task) => {
    if (props.modelValue) resetForm(task)
  },
)

function saveTask() {
  if (!form.title.trim()) {
    ElMessage.warning('Please enter a task title.')
    return
  }

  emit('save', {
    ...form,
    title: form.title.trim(),
    category: form.category.trim(),
    course: form.course || '',
    notes: form.notes.trim(),
    estimatedMinutes: form.estimatedMinutes === null ? null : Number(form.estimatedMinutes) || null,
  })

  visible.value = false
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="form.id ? 'Edit task' : 'Add task'"
    width="560px"
    destroy-on-close
  >
    <el-form label-position="top" class="task-form">
      <el-form-item label="Task title">
        <el-input v-model="form.title" placeholder="e.g., Finish HCI prototype" />
      </el-form-item>

      <div class="form-grid">
        <el-form-item label="Priority">
          <el-select v-model="form.priority" placeholder="Select priority">
            <el-option label="High" value="High" />
            <el-option label="Medium" value="Medium" />
            <el-option label="Low" value="Low" />
          </el-select>
        </el-form-item>

        <el-form-item label="Due date">
          <el-date-picker
            v-model="form.dueDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="Choose date"
            class="full-width"
          />
        </el-form-item>
      </div>

      <div class="form-grid">
        <el-form-item label="Category">
          <el-input v-model="form.category" placeholder="Project, Review, Reading" />
        </el-form-item>

        <el-form-item label="Course">
          <el-select v-model="form.course" clearable placeholder="Optional course">
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.name"
            />
          </el-select>
        </el-form-item>
      </div>

      <el-form-item label="Estimated study time (optional)">
        <el-input-number
          v-model="form.estimatedMinutes"
          :min="15"
          :max="360"
          :step="15"
          controls-position="right"
          placeholder="Optional"
        />
        <span class="time-hint">minutes</span>
        <el-button v-if="form.estimatedMinutes !== null" text type="primary" @click="form.estimatedMinutes = null">
          Clear
        </el-button>
      </el-form-item>

      <el-form-item label="Notes">
        <el-input
          v-model="form.notes"
          type="textarea"
          :rows="3"
          placeholder="Optional notes"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">Cancel</el-button>
      <el-button type="primary" @click="saveTask">Save task</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.task-form {
  display: grid;
  gap: 2px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.full-width {
  width: 100%;
}

.time-hint {
  margin-left: 10px;
  color: var(--text-muted);
}

@media (max-width: 620px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
