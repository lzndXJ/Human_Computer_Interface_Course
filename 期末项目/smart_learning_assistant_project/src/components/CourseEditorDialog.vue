<script setup>
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  course: {
    type: Object,
    default: null,
  },
  courses: {
    type: Array,
    default: () => [],
  },
  weekDays: {
    type: Array,
    default: () => [],
  },
  lessonPeriods: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue', 'save'])

const colorOptions = [
  { label: 'Green', value: '#2f7d68' },
  { label: 'Blue', value: '#3867d6' },
  { label: 'Amber', value: '#8a5a00' },
  { label: 'Red', value: '#9b3d3a' },
  { label: 'Steel', value: '#4c6a8a' },
  { label: 'Purple', value: '#6f4bb2' },
]

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const form = reactive(createEmptyCourse())

function createEmptyCourse() {
  return {
    id: '',
    name: '',
    color: '#2f7d68',
    timeSlots: [createEmptyTimeSlot()],
  }
}

function createEmptyTimeSlot(day = 'Monday') {
  return {
    localId: `slot-${Date.now()}-${Math.random()}`,
    day,
    startPeriod: 1,
    endPeriod: 1,
    room: '',
  }
}

function resetForm(course) {
  const emptyCourse = createEmptyCourse()

  form.id = course?.id || ''
  form.name = course?.name || ''
  form.color = course?.color || emptyCourse.color
  form.timeSlots = createTimeSlots(course)
}

function createTimeSlots(course) {
  if (Array.isArray(course?.timeSlots) && course.timeSlots.length) {
    return course.timeSlots.map((slot) => ({
      ...createEmptyTimeSlot(slot.day),
      ...slot,
      startPeriod: getPeriodIndex(slot.startPeriod, slot.startTime, 'startTime'),
      endPeriod: getPeriodIndex(slot.endPeriod, slot.endTime, 'endTime'),
    }))
  }

  return [
    {
      ...createEmptyTimeSlot(course?.day || 'Monday'),
      startPeriod: getPeriodIndex(course?.startPeriod, course?.startTime, 'startTime'),
      endPeriod: getPeriodIndex(course?.endPeriod, course?.endTime, 'endTime'),
      room: course?.room || '',
    },
  ]
}

function getPeriodIndex(periodIndex, time, fieldName) {
  const requestedIndex = Number(periodIndex)
  if (props.lessonPeriods.some((period) => period.index === requestedIndex)) return requestedIndex

  const matchedPeriod = props.lessonPeriods.find((period) => period[fieldName] === time)
  return matchedPeriod?.index || props.lessonPeriods[0]?.index || 1
}

watch(
  () => props.modelValue,
  (isVisible) => {
    if (isVisible) resetForm(props.course)
  },
)

watch(
  () => props.course,
  (course) => {
    if (props.modelValue) resetForm(course)
  },
)

function saveCourse() {
  if (!form.name.trim()) {
    ElMessage.warning('Please enter a course name.')
    return
  }

  for (const slot of form.timeSlots) {
    if (!slot.day || !slot.startPeriod || !slot.endPeriod) {
      ElMessage.warning('Please complete every time slot.')
      return
    }

    if (Number(slot.startPeriod) > Number(slot.endPeriod)) {
      ElMessage.warning('The ending period should not be earlier than the starting period.')
      return
    }
  }

  const cleanSlots = form.timeSlots.map((slot) => {
    const startPeriod = Number(slot.startPeriod)
    const endPeriod = Number(slot.endPeriod)
    const startSlot = props.lessonPeriods.find((period) => period.index === startPeriod)
    const endSlot = props.lessonPeriods.find((period) => period.index === endPeriod)

    return {
      day: slot.day,
      startPeriod,
      endPeriod,
      startTime: startSlot?.startTime || '',
      endTime: endSlot?.endTime || '',
      room: slot.room.trim(),
    }
  })

  emit('save', {
    id: form.id,
    name: form.name.trim(),
    color: form.color,
    day: cleanSlots[0].day,
    startTime: cleanSlots[0].startTime,
    endTime: cleanSlots[0].endTime,
    room: cleanSlots[0].room,
    timeSlots: cleanSlots,
  })

  visible.value = false
}

function addTimeSlot() {
  const lastSlot = form.timeSlots[form.timeSlots.length - 1]
  form.timeSlots.push({
    ...createEmptyTimeSlot(lastSlot?.day || 'Monday'),
    startPeriod: lastSlot?.startPeriod || 1,
    endPeriod: lastSlot?.endPeriod || lastSlot?.startPeriod || 1,
    room: lastSlot?.room || '',
  })
}

function removeTimeSlot(index) {
  if (form.timeSlots.length === 1) {
    ElMessage.warning('A course needs at least one time slot.')
    return
  }

  form.timeSlots.splice(index, 1)
}

function slotOverlapMessage(slot, index) {
  if (!slot.day || !slot.startPeriod || !slot.endPeriod || Number(slot.startPeriod) > Number(slot.endPeriod)) return ''

  const existingCourse = props.courses.find((course) => {
    if (course.id === form.id || course.day !== slot.day) return false
    return Number(slot.startPeriod) <= Number(course.endPeriod) && Number(slot.endPeriod) >= Number(course.startPeriod)
  })

  if (existingCourse) return `This overlaps with ${existingCourse.name}.`

  const siblingIndex = form.timeSlots.findIndex((otherSlot, otherIndex) => {
    if (otherIndex === index || otherSlot.day !== slot.day) return false
    return Number(slot.startPeriod) <= Number(otherSlot.endPeriod) && Number(slot.endPeriod) >= Number(otherSlot.startPeriod)
  })

  return siblingIndex >= 0 ? 'This overlaps with another time slot in this course.' : ''
}

function periodLabel(period) {
  return `Period ${period.index} (${period.startTime} - ${period.endTime})`
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="form.id ? 'Edit course' : 'Add course'"
    width="560px"
    destroy-on-close
  >
    <el-form label-position="top" class="course-form">
      <el-form-item label="Course name">
        <el-input v-model="form.name" placeholder="e.g., Human-Computer Interaction" />
      </el-form-item>

      <el-form-item label="Color">
        <div class="color-swatches">
          <button
            v-for="color in colorOptions"
            :key="color.value"
            type="button"
            class="color-swatch"
            :class="{ selected: form.color === color.value }"
            :style="{ backgroundColor: color.value }"
            :aria-label="color.label"
            @click="form.color = color.value"
          ></button>
        </div>
      </el-form-item>

      <div class="time-slot-header">
        <h3>Time slots</h3>
        <el-button :icon="Plus" @click="addTimeSlot">Add time</el-button>
      </div>

      <section
        v-for="(slot, index) in form.timeSlots"
        :key="slot.localId"
        class="time-slot"
      >
        <div class="slot-title">
          <strong>Time slot {{ index + 1 }}</strong>
          <el-button
            v-if="form.timeSlots.length > 1"
            :icon="Delete"
            circle
            text
            type="danger"
            @click="removeTimeSlot(index)"
          />
        </div>

        <div class="form-grid">
          <el-form-item label="Day">
            <el-select v-model="slot.day" placeholder="Choose day">
              <el-option v-for="day in weekDays" :key="day" :label="day" :value="day" />
            </el-select>
          </el-form-item>

          <el-form-item label="Room / Location">
            <el-input v-model="slot.room" placeholder="e.g., Design Lab 204" />
          </el-form-item>
        </div>

        <div class="form-grid">
          <el-form-item label="Start period">
            <el-select v-model="slot.startPeriod" class="full-width" placeholder="Start period">
              <el-option
                v-for="period in lessonPeriods"
                :key="period.index"
                :label="periodLabel(period)"
                :value="period.index"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="End period">
            <el-select v-model="slot.endPeriod" class="full-width" placeholder="End period">
              <el-option
                v-for="period in lessonPeriods"
                :key="period.index"
                :label="periodLabel(period)"
                :value="period.index"
              />
            </el-select>
          </el-form-item>
        </div>

        <el-alert
          v-if="slotOverlapMessage(slot, index)"
          type="warning"
          :closable="false"
          show-icon
          :title="slotOverlapMessage(slot, index)"
        />
      </section>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">Cancel</el-button>
      <el-button type="primary" @click="saveCourse">Save course</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.course-form {
  display: grid;
  gap: 2px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.color-swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.full-width {
  width: 100%;
}

.color-swatch {
  width: 34px;
  height: 34px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
}

.color-swatch.selected {
  border-color: var(--text-strong);
  box-shadow: 0 0 0 3px #ffffff inset;
}

.time-slot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 4px;
}

.time-slot-header h3 {
  margin: 0;
  color: var(--text-strong);
  font-size: 1rem;
  font-weight: 800;
}

.time-slot {
  display: grid;
  gap: 2px;
  padding: 14px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #fbfcfc;
}

.slot-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 32px;
}

.slot-title strong {
  color: var(--text-strong);
  font-weight: 800;
}

@media (max-width: 620px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
