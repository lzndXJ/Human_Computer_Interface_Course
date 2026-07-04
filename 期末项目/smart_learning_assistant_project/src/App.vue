<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { Calendar, Checked, Collection, Compass, House } from '@element-plus/icons-vue'

const navItems = [
  { label: 'Dashboard', to: '/', icon: House },
  { label: 'Schedule', to: '/schedule', icon: Calendar },
  { label: 'Tasks', to: '/tasks', icon: Checked },
  { label: 'Resources', to: '/resources', icon: Collection },
  { label: 'Planner', to: '/planner', icon: Compass },
]

</script>

<template>
  <div class="app-shell">
    <header class="top-nav">
      <div class="nav-pill">
        <RouterLink to="/" class="brand-link">
          <span class="brand-mark">SLA</span>
          <span>
            <strong>Smart Learning</strong>
            <small>Assistant</small>
          </span>
        </RouterLink>

        <nav class="nav-list" aria-label="Main navigation">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            exact-active-class="is-active"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>

      </div>
    </header>

    <main class="content-area">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--app-background);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 16px 14px 8px;
  background: linear-gradient(180deg, rgba(246, 247, 249, 0.98), rgba(246, 247, 249, 0.72));
  backdrop-filter: blur(12px);
}

.nav-pill {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 34px;
  max-width: 1720px;
  min-height: 76px;
  margin: 0 auto;
  padding: 12px 20px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 42px rgba(28, 37, 34, 0.08);
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 14px;
  color: var(--text-strong);
  text-decoration: none;
  white-space: nowrap;
}

.brand-link strong,
.brand-link small {
  display: block;
}

.brand-link small {
  color: var(--text-muted);
  font-size: 0.92rem;
  margin-top: 2px;
}

.brand-link strong {
  font-size: 1.08rem;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 8px;
  background: #2f7d68;
  color: #ffffff;
  font-weight: 800;
  letter-spacing: 0;
}

.nav-list {
  display: flex;
  justify-content: center;
  gap: 12px;
  min-width: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 46px;
  padding: 10px 16px;
  border-radius: 8px;
  color: var(--text-muted);
  text-decoration: none;
  font-weight: 600;
  font-size: 1.02rem;
  white-space: nowrap;
}

.nav-link:hover,
.nav-link.is-active {
  background: #eaf5f0;
  color: #216450;
}

.content-area {
  width: min(96vw, 1720px);
  max-width: none;
  margin: 0 auto;
  padding: 28px 14px 40px;
}

@media (max-width: 1080px) {
  .nav-pill {
    grid-template-columns: 1fr auto;
    gap: 12px;
  }

  .nav-list {
    grid-column: 1 / -1;
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 2px;
  }
}

@media (max-width: 640px) {
  .top-nav {
    padding: 10px 10px 4px;
  }

  .nav-pill {
    display: flex;
    flex-wrap: wrap;
  }

  .brand-link {
    flex: 1 1 100%;
  }

  .nav-list {
    order: 3;
    width: 100%;
  }

  .nav-link {
    flex: 0 0 auto;
  }

  .content-area {
    width: 100%;
    padding: 20px 10px 32px;
  }
}
</style>
