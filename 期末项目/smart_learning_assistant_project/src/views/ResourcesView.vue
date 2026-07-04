<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Link, Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { loadLearningData, saveLearningSection } from '@/utils/storage'

const initialData = loadLearningData()
const courses = ref(initialData.courses)
const resources = ref(initialData.resources)

const dialogVisible = ref(false)
const editingResourceId = ref('')
const keyword = ref('')
const courseFilter = ref('all')

const form = reactive(createEmptyResource())

const courseOptions = computed(() => {
  const names = new Set([
    ...courses.value.map((course) => course.name),
    ...resources.value.map((resource) => resource.course).filter(Boolean),
  ])

  return Array.from(names).sort()
})

const filteredResources = computed(() => {
  const query = keyword.value.trim().toLowerCase()

  return resources.value.filter((resource) => {
    const matchesCourse = courseFilter.value === 'all' || resource.course === courseFilter.value
    const searchableText = `${resource.title} ${resource.type} ${resource.course} ${resource.note}`.toLowerCase()
    return matchesCourse && (!query || searchableText.includes(query))
  })
})

function createEmptyResource() {
  return {
    title: '',
    course: '',
    type: 'Reference',
    url: 'https://example.com',
    note: '',
  }
}

function openAddDialog() {
  editingResourceId.value = ''
  Object.assign(form, createEmptyResource())
  dialogVisible.value = true
}

function openEditDialog(resource) {
  editingResourceId.value = resource.id
  Object.assign(form, resource)
  dialogVisible.value = true
}

function saveResource() {
  if (!form.title.trim()) {
    ElMessage.warning('Please enter a resource title.')
    return
  }

  const resourceData = {
    ...form,
    title: form.title.trim(),
    course: form.course || '',
    note: form.note.trim(),
  }

  if (editingResourceId.value) {
    resources.value = resources.value.map((resource) =>
      resource.id === editingResourceId.value ? { ...resourceData, id: resource.id } : resource,
    )
    ElMessage.success('Resource updated.')
  } else {
    resources.value = [{ ...resourceData, id: `resource-${Date.now()}` }, ...resources.value]
    ElMessage.success('Resource added.')
  }

  saveLearningSection('resources', resources.value)
  dialogVisible.value = false
}

function deleteResource(resourceId) {
  ElMessageBox.confirm('This resource will be removed from your local list.', 'Delete resource?', {
    confirmButtonText: 'Delete',
    cancelButtonText: 'Cancel',
    type: 'warning',
  })
    .then(() => {
      resources.value = resources.value.filter((resource) => resource.id !== resourceId)
      saveLearningSection('resources', resources.value)
      ElMessage.success('Resource deleted.')
    })
    .catch(() => {})
}

function typeTag(type) {
  return {
    Reference: 'primary',
    Tool: 'success',
    Note: 'warning',
    Reading: 'info',
  }[type] || 'info'
}

</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="Resource center"
      title="Course resources and reminders"
      description="Collect links, notes, and tools by course while keeping urgent deadlines visible."
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openAddDialog">Add resource</el-button>
      </template>
    </PageHeader>

    <div class="resource-layout">
      <section class="panel">
        <div class="resource-toolbar">
          <div>
            <h2 class="section-title">Learning Resources</h2>
            <p class="muted-text">{{ filteredResources.length }} resource(s) shown</p>
          </div>

          <div class="filters">
            <el-input v-model="keyword" clearable placeholder="Search resources" />
            <el-select v-model="courseFilter" class="course-select" aria-label="Course filter">
              <el-option label="All courses" value="all" />
              <el-option
                v-for="course in courseOptions"
                :key="course"
                :label="course"
                :value="course"
              />
            </el-select>
          </div>
        </div>

        <div v-if="filteredResources.length" class="resource-grid">
          <article
            v-for="resource in filteredResources"
            :key="resource.id"
            class="resource-card"
            role="button"
            tabindex="0"
            @click="openEditDialog(resource)"
            @keydown.enter="openEditDialog(resource)"
          >
            <div class="resource-head">
              <div>
                <h3>{{ resource.title }}</h3>
                <div class="resource-meta">
                  <el-tag size="small" :type="typeTag(resource.type)">{{ resource.type }}</el-tag>
                  <span>{{ resource.course || 'No course linked' }}</span>
                </div>
              </div>

              <div class="card-actions">
                <el-tooltip content="Open resource" placement="top">
                  <el-button
                    :icon="Link"
                    circle
                    text
                    tag="a"
                    :href="resource.url"
                    target="_blank"
                    @click.stop
                  />
                </el-tooltip>
                <el-tooltip content="Delete resource" placement="top">
                  <el-button :icon="Delete" circle text type="danger" @click.stop="deleteResource(resource.id)" />
                </el-tooltip>
              </div>
            </div>

            <p>{{ resource.note || 'No note added yet.' }}</p>
          </article>
        </div>

        <EmptyState v-else description="No resources match the current filters.">
          <el-button type="primary" :icon="Plus" @click="openAddDialog">Add resource</el-button>
        </EmptyState>
      </section>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingResourceId ? 'Edit resource' : 'Add resource'"
      width="560px"
      destroy-on-close
    >
      <el-form label-position="top" class="resource-form">
        <el-form-item label="Resource title">
          <el-input v-model="form.title" placeholder="e.g., Vue Router notes" />
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="Course">
            <el-select v-model="form.course" clearable filterable allow-create placeholder="Optional course">
              <el-option v-for="course in courseOptions" :key="course" :label="course" :value="course" />
            </el-select>
          </el-form-item>

          <el-form-item label="Type">
            <el-select v-model="form.type">
              <el-option label="Reference" value="Reference" />
              <el-option label="Tool" value="Tool" />
              <el-option label="Note" value="Note" />
              <el-option label="Reading" value="Reading" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="URL">
          <el-input v-model="form.url" placeholder="https://example.com" />
        </el-form-item>

        <el-form-item label="Note">
          <el-input v-model="form.note" type="textarea" :rows="3" placeholder="Why this resource is useful" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveResource">Save resource</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.resource-layout {
  display: block;
}

.resource-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(300px, 420px);
  gap: 16px;
  align-items: end;
  margin-bottom: 18px;
}

.filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 160px;
  gap: 10px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.resource-card {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #ffffff;
}

.resource-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.resource-card:hover {
  border-color: #99cabb;
  box-shadow: 0 8px 24px rgba(33, 100, 80, 0.08);
  transform: translateY(-1px);
}

.resource-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

h3 {
  margin: 0;
  color: var(--text-strong);
  font-size: 1rem;
  font-weight: 800;
}

.resource-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 0.88rem;
}

.resource-card p {
  margin: 0;
  color: var(--text-muted);
}

.card-actions {
  display: flex;
  flex-shrink: 0;
  gap: 2px;
}

.resource-form {
  display: grid;
  gap: 2px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

@media (max-width: 980px) {
  .resource-toolbar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .filters,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
