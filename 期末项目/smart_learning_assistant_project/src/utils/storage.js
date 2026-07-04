const STORAGE_KEY = 'smart-learning-assistant-data'

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const defaultLessonPeriods = [
  { index: 1, startTime: '08:00', endTime: '08:45' },
  { index: 2, startTime: '08:55', endTime: '09:40' },
  { index: 3, startTime: '10:00', endTime: '10:45' },
  { index: 4, startTime: '10:55', endTime: '11:40' },
  { index: 5, startTime: '14:00', endTime: '14:45' },
  { index: 6, startTime: '14:55', endTime: '15:40' },
  { index: 7, startTime: '16:00', endTime: '16:45' },
  { index: 8, startTime: '16:55', endTime: '17:40' },
  { index: 9, startTime: '19:00', endTime: '19:45' },
  { index: 10, startTime: '19:55', endTime: '20:40' },
  { index: 11, startTime: '20:50', endTime: '21:35' },
]

export function getTodayISO() {
  return toLocalISODate(new Date())
}

function addDaysISO(daysToAdd) {
  const date = new Date()
  date.setDate(date.getDate() + daysToAdd)
  return toLocalISODate(date)
}

function toLocalISODate(date) {
  const localDate = new Date(date)
  localDate.setMinutes(localDate.getMinutes() - localDate.getTimezoneOffset())
  return localDate.toISOString().slice(0, 10)
}

export function getWeekDays() {
  return days
}

export function getDefaultLessonPeriods() {
  return defaultLessonPeriods.map((period) => ({ ...period }))
}

export function createDefaultData() {
  const today = getTodayISO()

  return {
    lessonPeriods: getDefaultLessonPeriods(),
    courses: [
      {
        id: 'course-hci',
        name: 'Human-Computer Interaction',
        day: 'Monday',
        startPeriod: 2,
        endPeriod: 3,
        startTime: '08:55',
        endTime: '10:45',
        room: 'Design Lab 204',
        color: '#2f7d68',
      },
      {
        id: 'course-data',
        name: 'Data Visualization',
        day: 'Tuesday',
        startPeriod: 5,
        endPeriod: 6,
        startTime: '14:00',
        endTime: '15:40',
        room: 'Room B305',
        color: '#3867d6',
      },
      {
        id: 'course-web',
        name: 'Web Development',
        day: 'Wednesday',
        startPeriod: 3,
        endPeriod: 4,
        startTime: '10:00',
        endTime: '11:40',
        room: 'Computer Lab 2',
        color: '#8a5a00',
      },
      {
        id: 'course-english',
        name: 'Academic English',
        day: 'Friday',
        startPeriod: 1,
        endPeriod: 2,
        startTime: '08:00',
        endTime: '09:40',
        room: 'Room A112',
        color: '#9b3d3a',
      },
      {
        id: 'course-project',
        name: 'Project Review Session',
        day: 'Sunday',
        startPeriod: 7,
        endPeriod: 8,
        startTime: '16:00',
        endTime: '17:40',
        room: 'Online',
        color: '#4c6a8a',
      },
    ],
    tasks: [
      {
        id: 'task-hci-notes',
        title: 'Review HCI lecture notes',
        course: 'Human-Computer Interaction',
        category: 'Review',
        priority: 'High',
        dueDate: today,
        completed: false,
        estimatedMinutes: 45,
        notes: 'Focus on usability heuristics and cognitive load.',
      },
      {
        id: 'task-prototype-flow',
        title: 'Sketch planner interaction flow',
        course: 'Human-Computer Interaction',
        category: 'Project',
        priority: 'High',
        dueDate: today,
        completed: false,
        estimatedMinutes: 90,
        notes: 'Keep the guided flow simple and demo-friendly.',
      },
      {
        id: 'task-web-practice',
        title: 'Practice Vue component props',
        course: 'Web Development',
        category: 'Practice',
        priority: 'Medium',
        dueDate: addDaysISO(1),
        completed: false,
        estimatedMinutes: 60,
        notes: '',
      },
      {
        id: 'task-reading',
        title: 'Read article about dashboard design',
        course: '',
        category: 'Reading',
        priority: 'Low',
        dueDate: addDaysISO(2),
        completed: true,
        estimatedMinutes: 30,
        notes: '',
      },
    ],
    resources: [
      {
        id: 'resource-vue-guide',
        title: 'Vue3 Composition API Guide',
        course: 'Web Development',
        type: 'Reference',
        url: 'https://vuejs.org/guide/introduction.html',
        note: 'Core concepts for building the task and resource modules.',
      },
      {
        id: 'resource-element-plus',
        title: 'Element Plus Components',
        course: 'Human-Computer Interaction',
        type: 'Tool',
        url: 'https://element-plus.org/',
        note: 'Useful UI components for forms, dialogs, tags, and navigation.',
      },
      {
        id: 'resource-report-outline',
        title: 'Final Report Outline',
        course: 'Project Review Session',
        type: 'Note',
        url: 'https://example.com/report-outline',
        note: 'User needs, modules, interaction design, limitations, improvements, and contribution.',
      },
    ],
    plans: [],
  }
}

export function loadLearningData() {
  const defaults = createDefaultData()
  const rawData = localStorage.getItem(STORAGE_KEY)

  if (!rawData) {
    saveLearningData(defaults)
    return defaults
  }

  try {
    const savedData = JSON.parse(rawData)
    const lessonPeriods = normalizeLessonPeriods(savedData.lessonPeriods)

    return {
      ...defaults,
      ...savedData,
      lessonPeriods,
      courses: Array.isArray(savedData.courses)
        ? normalizeCourses(savedData.courses, lessonPeriods)
        : defaults.courses,
      tasks: Array.isArray(savedData.tasks)
        ? savedData.tasks
        : defaults.tasks,
      resources: Array.isArray(savedData.resources) ? savedData.resources : defaults.resources,
      plans: Array.isArray(savedData.plans) ? savedData.plans : defaults.plans,
    }
  } catch (error) {
    console.warn('Learning data was reset because localStorage could not be parsed.', error)
    saveLearningData(defaults)
    return defaults
  }
}

export function saveLearningData(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

export function saveLearningSection(sectionName, sectionValue) {
  const currentData = loadLearningData()
  saveLearningData({
    ...currentData,
    [sectionName]: sectionValue,
  })
}

function normalizeLessonPeriods(savedPeriods) {
  if (!Array.isArray(savedPeriods) || !savedPeriods.length) return getDefaultLessonPeriods()

  return getDefaultLessonPeriods().map((defaultPeriod) => {
    const savedPeriod = savedPeriods.find((period) => Number(period.index) === defaultPeriod.index)

    return {
      ...defaultPeriod,
      startTime: savedPeriod?.startTime || defaultPeriod.startTime,
      endTime: savedPeriod?.endTime || defaultPeriod.endTime,
    }
  })
}

function normalizeCourses(courses, lessonPeriods) {
  return courses.map((course) => {
    const inferredStartPeriod = getPeriodFromTime(course.startTime, lessonPeriods, 'startTime')
    const inferredEndPeriod = getPeriodFromTime(course.endTime, lessonPeriods, 'endTime')
    const startPeriod = Number(course.startPeriod || inferredStartPeriod || 1)
    const endPeriod = Number(course.endPeriod || inferredEndPeriod || startPeriod)
    const safeEndPeriod = Math.max(startPeriod, endPeriod)
    const startSlot = lessonPeriods.find((period) => period.index === startPeriod)
    const endSlot = lessonPeriods.find((period) => period.index === safeEndPeriod)

    return {
      ...course,
      startPeriod,
      endPeriod: safeEndPeriod,
      startTime: startSlot?.startTime || course.startTime,
      endTime: endSlot?.endTime || course.endTime,
    }
  })
}

function getPeriodFromTime(time, lessonPeriods, fieldName) {
  if (!time) return null

  const exactPeriod = lessonPeriods.find((period) => period[fieldName] === time)
  if (exactPeriod) return exactPeriod.index

  const timeMinutes = toMinutes(time)
  if (Number.isNaN(timeMinutes)) return null

  return lessonPeriods.reduce((closestPeriod, period) => {
    const closestDistance = Math.abs(toMinutes(closestPeriod[fieldName]) - timeMinutes)
    const periodDistance = Math.abs(toMinutes(period[fieldName]) - timeMinutes)
    return periodDistance < closestDistance ? period : closestPeriod
  }, lessonPeriods[0])?.index
}

function toMinutes(time) {
  const [hours, minutes] = String(time).split(':').map(Number)
  return hours * 60 + minutes
}
