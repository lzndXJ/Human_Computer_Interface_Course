<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Delete, Edit, Plus } from '@element-plus/icons-vue'
import CourseEditorDialog from '@/components/CourseEditorDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import { getWeekDays, loadLearningData, saveLearningSection } from '@/utils/storage'

const initialData = loadLearningData()
const courses = ref(initialData.courses)
const tasks = ref(initialData.tasks)
const lessonPeriods = ref(initialData.lessonPeriods)
const weekDays = getWeekDays()
const dialogVisible = ref(false)
const periodDialogVisible = ref(false)
const editingCourse = ref(null)
const editingPeriod = reactive({
  index: 1,
  startTime: '08:00',
  endTime: '08:45',
})

const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' })

const totalClasses = computed(() => courses.value.length)

const sortedCourses = computed(() =>
  courses.value
    .filter((course) => weekDays.includes(course.day))
    .sort((a, b) => weekDays.indexOf(a.day) - weekDays.indexOf(b.day) || Number(a.startPeriod) - Number(b.startPeriod)),
)

function openAddDialog(day = todayName, periodIndex = 1) {
  editingCourse.value = {
    day,
    startPeriod: periodIndex,
    endPeriod: periodIndex,
  }
  dialogVisible.value = true
}

function openEditDialog(course) {
  editingCourse.value = { ...course }
  dialogVisible.value = true
}

function saveCourse(courseData) {
  const previousCourse = courses.value.find((course) => course.id === courseData.id)
  const timeSlots = courseData.timeSlots?.length ? courseData.timeSlots : [courseData]

  if (courseData.id) {
    const [firstSlot, ...extraSlots] = timeSlots
    const updatedCourse = buildCourseFromSlot(courseData, firstSlot, courseData.id)

    courses.value = courses.value.map((course) =>
      course.id === courseData.id ? updatedCourse : course,
    )

    if (extraSlots.length) {
      courses.value = [
        ...courses.value,
        ...extraSlots.map((slot, index) => buildCourseFromSlot(courseData, slot, `course-${Date.now()}-${index}`)),
      ]
    }

    ElMessage.success('Course updated.')
  } else {
    courses.value = [
      ...courses.value,
      ...timeSlots.map((slot, index) => buildCourseFromSlot(courseData, slot, `course-${Date.now()}-${index}`)),
    ]
    ElMessage.success('Course added.')
  }

  saveLearningSection('courses', courses.value)

  if (previousCourse && previousCourse.name !== courseData.name) {
    tasks.value = tasks.value.map((task) =>
      task.course === previousCourse.name ? { ...task, course: courseData.name } : task,
    )
    saveLearningSection('tasks', tasks.value)
  }
}

function buildCourseFromSlot(courseData, slot, id) {
  return {
    id,
    name: courseData.name,
    day: slot.day,
    startPeriod: slot.startPeriod,
    endPeriod: slot.endPeriod,
    startTime: slot.startTime,
    endTime: slot.endTime,
    room: slot.room,
    color: courseData.color,
  }
}

function deleteCourse(courseId) {
  ElMessageBox.confirm('This course will be removed from your weekly schedule.', 'Delete course?', {
    confirmButtonText: 'Delete',
    cancelButtonText: 'Cancel',
    type: 'warning',
  })
    .then(() => {
      const deletedCourse = courses.value.find((course) => course.id === courseId)
      courses.value = courses.value.filter((course) => course.id !== courseId)
      saveLearningSection('courses', courses.value)

      if (deletedCourse) {
        tasks.value = tasks.value.map((task) =>
          task.course === deletedCourse.name ? { ...task, course: '' } : task,
        )
        saveLearningSection('tasks', tasks.value)
      }

      ElMessage.success('Course deleted.')
    })
    .catch(() => {})
}

function dayGridColumn(day) {
  return weekDays.indexOf(day) + 2
}

function courseGridStyle(course) {
  const startPeriod = Number(course.startPeriod || 1)
  const endPeriod = Math.max(startPeriod, Number(course.endPeriod || startPeriod))

  return {
    gridColumn: String(dayGridColumn(course.day)),
    gridRow: `${startPeriod + 1} / ${endPeriod + 2}`,
    borderLeftColor: course.color,
  }
}

function cellGridStyle(day, period) {
  return {
    gridColumn: String(dayGridColumn(day)),
    gridRow: String(period.index + 1),
  }
}

function periodGridStyle(period) {
  return {
    gridColumn: '1',
    gridRow: String(period.index + 1),
  }
}

function openPeriodDialog(period) {
  editingPeriod.index = period.index
  editingPeriod.startTime = period.startTime
  editingPeriod.endTime = period.endTime
  periodDialogVisible.value = true
}

function savePeriod() {
  if (!editingPeriod.startTime || !editingPeriod.endTime) {
    ElMessage.warning('Please complete the period time.')
    return
  }

  if (editingPeriod.startTime >= editingPeriod.endTime) {
    ElMessage.warning('The end time should be later than the start time.')
    return
  }

  lessonPeriods.value = lessonPeriods.value.map((period) =>
    period.index === editingPeriod.index
      ? {
          ...period,
          startTime: editingPeriod.startTime,
          endTime: editingPeriod.endTime,
        }
      : period,
  )
  courses.value = syncCourseTimes(courses.value)
  saveLearningSection('lessonPeriods', lessonPeriods.value)
  saveLearningSection('courses', courses.value)
  periodDialogVisible.value = false
  ElMessage.success('Period time updated.')
}

function syncCourseTimes(courseList) {
  return courseList.map((course) => {
    const startPeriod = lessonPeriods.value.find((period) => period.index === Number(course.startPeriod))
    const endPeriod = lessonPeriods.value.find((period) => period.index === Number(course.endPeriod))

    return {
      ...course,
      startTime: startPeriod?.startTime || course.startTime,
      endTime: endPeriod?.endTime || course.endTime,
    }
  })
}
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="Weekly view"
      title="Class schedule"
      description="A simple weekly structure for seeing where study tasks can fit around classes."
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openAddDialog()">Add course</el-button>
        <el-tag type="success" effect="plain">
          <el-icon><Calendar /></el-icon>
          {{ totalClasses }} classes
        </el-tag>
      </template>
    </PageHeader>

    <section class="schedule-board" :style="{ '--period-count': lessonPeriods.length }">
      <div class="board-corner">Periods</div>

      <div
        v-for="day in weekDays"
        :key="day"
        class="day-heading"
        :class="{ 'is-today': day === todayName }"
        :style="{ gridColumn: String(dayGridColumn(day)), gridRow: '1' }"
      >
        <h2>{{ day }}</h2>
        <div class="day-actions">
          <el-tag v-if="day === todayName" size="small" type="success">Today</el-tag>
          <el-tooltip content="Add course to this day" placement="top">
            <el-button :icon="Plus" circle text size="small" @click="openAddDialog(day)" />
          </el-tooltip>
        </div>
      </div>

      <button
        v-for="period in lessonPeriods"
        :key="period.index"
        type="button"
        class="period-cell"
        :style="periodGridStyle(period)"
        @click="openPeriodDialog(period)"
      >
        <strong>Period {{ period.index }}</strong>
        <span>{{ period.startTime }} - {{ period.endTime }}</span>
        <el-icon><Edit /></el-icon>
      </button>

      <template v-for="period in lessonPeriods" :key="`cells-${period.index}`">
        <button
          v-for="day in weekDays"
          :key="`${day}-${period.index}`"
          type="button"
          class="schedule-cell"
          :style="cellGridStyle(day, period)"
          :aria-label="`Add course on ${day}, period ${period.index}`"
          @click="openAddDialog(day, period.index)"
        ></button>
      </template>

      <div
        v-for="course in sortedCourses"
        :key="course.id"
        class="course-card"
        :style="courseGridStyle(course)"
        role="button"
        tabindex="0"
        @click="openEditDialog(course)"
        @keydown.enter="openEditDialog(course)"
      >
        <div class="course-content">
          <span>
            Period {{ course.startPeriod }}<template v-if="course.endPeriod !== course.startPeriod">-{{ course.endPeriod }}</template>
            / {{ course.startTime }} - {{ course.endTime }}
          </span>
          <strong>{{ course.name }}</strong>
          <p>{{ course.room || 'Location not set' }}</p>
        </div>

        <div class="course-actions">
          <el-tooltip content="Delete course" placement="top">
            <el-button
              :icon="Delete"
              circle
              text
              type="danger"
              size="small"
              @click.stop="deleteCourse(course.id)"
            />
          </el-tooltip>
        </div>
      </div>
    </section>

    <CourseEditorDialog
      v-model="dialogVisible"
      :course="editingCourse"
      :courses="courses"
      :week-days="weekDays"
      :lesson-periods="lessonPeriods"
      @save="saveCourse"
    />

    <el-dialog
      v-model="periodDialogVisible"
      :title="`Edit period ${editingPeriod.index}`"
      width="360px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="Start time">
          <el-time-select
            v-model="editingPeriod.startTime"
            start="06:00"
            step="00:05"
            end="23:55"
            class="full-width"
            placeholder="Start time"
          />
        </el-form-item>

        <el-form-item label="End time">
          <el-time-select
            v-model="editingPeriod.endTime"
            start="06:00"
            step="00:05"
            end="23:55"
            class="full-width"
            placeholder="End time"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="periodDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="savePeriod">Save period</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.schedule-board {
  display: grid;
  grid-template-columns: 132px repeat(7, minmax(154px, 1fr));
  grid-template-rows: 48px repeat(var(--period-count), 78px);
  position: relative;
  min-width: 1210px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--panel-background);
  overflow-x: auto;
  overflow-y: hidden;
}

.board-corner,
.day-heading,
.period-cell,
.schedule-cell {
  border: 1px solid var(--app-border);
  border-width: 0 1px 1px 0;
}

.board-corner {
  display: flex;
  align-items: center;
  justify-content: center;
  grid-column: 1;
  grid-row: 1;
  color: var(--text-muted);
  font-size: 0.86rem;
  font-weight: 800;
  background: #f8faf9;
}

.day-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  padding: 0 10px;
  background: #f8faf9;
}

.day-heading.is-today {
  background: #eef8f4;
}

.day-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

h2 {
  margin: 0;
  color: var(--text-strong);
  font-size: 0.94rem;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.period-cell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-content: center;
  gap: 0 8px;
  min-width: 0;
  padding: 8px 10px;
  color: var(--text-body);
  text-align: left;
  background: #fbfcfc;
  cursor: pointer;
}

.period-cell:hover {
  background: #edf5f2;
}

.period-cell strong {
  color: var(--text-strong);
  font-size: 0.9rem;
  font-weight: 800;
}

.period-cell span {
  grid-column: 1;
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.period-cell .el-icon {
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: center;
  color: var(--text-muted);
}

.schedule-cell {
  min-width: 0;
  background: #ffffff;
  cursor: pointer;
}

.schedule-cell:hover {
  background: #f1f7f5;
}

.course-card {
  position: relative;
  z-index: 2;
  min-width: 0;
  margin: 6px;
  padding: 12px 38px 12px 12px;
  border: 1px solid var(--app-border);
  border-left: 5px solid;
  border-radius: 8px;
  background: #ffffff;
  overflow: hidden;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.course-card:hover {
  border-color: #99cabb;
  box-shadow: 0 8px 24px rgba(33, 100, 80, 0.08);
  transform: translateY(-1px);
}

.course-content {
  min-width: 0;
}

.course-card span {
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.course-card strong {
  display: block;
  margin-top: 4px;
  color: var(--text-strong);
  font-size: 1.02rem;
  font-weight: 800;
  line-height: 1.35;
  overflow-wrap: break-word;
  word-break: normal;
  hyphens: auto;
}

.course-card p {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 0.86rem;
  overflow-wrap: anywhere;
}

.course-actions {
  display: flex;
  position: absolute;
  top: 8px;
  right: 8px;
  gap: 2px;
}

.full-width {
  width: 100%;
}

@media (hover: hover) {
  .course-actions {
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  .course-card:hover .course-actions,
  .course-card:focus-within .course-actions {
    opacity: 1;
  }
}
</style>
