# Smart Learning Assistant

Smart Learning Assistant is a Vue3 + Element Plus web system for university students. It connects class schedules, task management, dashboard analytics, guided planning, and resource reminders into one local demo application.

## Core Features

1. Task Management
   - Add, edit, delete, complete, and filter learning tasks.
   - Filter by status, priority, and course.
   - Store priority, due date, category, course, notes, and estimated study time.

2. Learning Dashboard
   - Show classes today, pending tasks, completion rate, study time, and saved resources.
   - Display course workload through a visual bar chart.
   - Show urgent deadline reminders for tasks due within three days.
   - Suggest the next learning step from task and schedule data.

3. Resource And Reminder Center
   - Add, edit, delete, search, and open study resources.
   - Organize resources by course and type.
   - Keep urgent deadlines visible next to related materials.

Extra module:

- Study Planner: a guided three-step planner with optional browser voice input.
- AI Study Suggestion: generate a short learning suggestion from current tasks, deadlines, workload, and resources. It uses a local fallback when the AI proxy is not running.

## Technology Stack

- Vue3
- Vue Router
- Element Plus
- Vite
- localStorage

## Project Setup

```sh
npm install
```

## Run For Development

```sh
npm run dev
```

On Windows PowerShell, use `npm.cmd` if direct `npm` is blocked:

```sh
npm.cmd run dev
```

## Optional AI Suggestion Server

The dashboard AI button works without an API key by using a local fallback suggestion. To call a real model, run a small local proxy server so the API key is not exposed in browser code.

The proxy uses an OpenAI-compatible Chat Completions API, so it can work with OpenAI, AIHubMix, ModelScope, or another compatible provider by changing environment variables.

### AIHubMix Example

cmd:

```cmd
set AI_PROVIDER=AIHubMix
set AI_BASE_URL=https://aihubmix.com/v1
set AI_API_KEY=your_aihubmix_key_here
set AI_MODEL=gpt-4o-mini
npm.cmd run ai-server
```

PowerShell:

```powershell
$env:AI_PROVIDER="AIHubMix"
$env:AI_BASE_URL="https://aihubmix.com/v1"
$env:AI_API_KEY="your_aihubmix_key_here"
$env:AI_MODEL="gpt-4o-mini"
npm.cmd run ai-server
```

### ModelScope Example

cmd:

```cmd
set AI_PROVIDER=ModelScope
set AI_BASE_URL=https://api-inference.modelscope.cn/v1
set AI_API_KEY=your_modelscope_key_here
set AI_MODEL=Qwen/Qwen3-30B-A3B-Instruct-2507
npm.cmd run ai-server
```

PowerShell:

```powershell
$env:AI_PROVIDER="ModelScope"
$env:AI_BASE_URL="https://api-inference.modelscope.cn/v1"
$env:AI_API_KEY="your_modelscope_key_here"
$env:AI_MODEL="Qwen/Qwen3-30B-A3B-Instruct-2507"
npm.cmd run ai-server
```

### OpenAI Example

PowerShell:

```sh
$env:AI_PROVIDER="OpenAI"
$env:AI_BASE_URL="https://api.openai.com/v1"
$env:AI_API_KEY="your_api_key_here"
$env:AI_MODEL="gpt-4o-mini"
npm.cmd run ai-server
```

In another terminal:

```sh
npm.cmd run dev
```

Then open the dashboard and click `Generate suggestion`.

Optional model override:

```sh
$env:AI_MODEL="your_model_name"
```

## Build For Submission

```sh
npm run build
```

## Data Storage

The demo uses browser `localStorage`. Data is saved locally on the current browser and device. If you need to reset the data, clear site data in the browser dev tools or change the storage key in `src/utils/storage.js`.

## Suggested Demo Flow

1. Open Dashboard and introduce the target user: university students managing classes, tasks, resources, and deadlines.
2. Show task management: add a task, filter by course or priority, and mark it completed.
3. Return to Dashboard to show updated progress, workload, and reminders.
4. Click the AI Study Suggestion button. If no API key is configured, explain that the system falls back to local rules for stable demonstration.
5. Open Resources to add a course material and explain the reminder center.
6. Open Planner to generate a study plan.

## Team Contribution Example

- Member A: app layout, router, schedule, and task management.
- Member B: dashboard statistics, workload visualization, completion logic, and reminders.
- Member C: resource center, planner polish, README, report, and presentation preparation.
