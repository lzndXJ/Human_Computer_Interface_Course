import http from 'node:http'

const PORT = Number(process.env.AI_SERVER_PORT || 8787)
const PROVIDER = process.env.AI_PROVIDER || detectProvider()
const API_KEY =
  process.env.AI_API_KEY ||
  process.env.AIHUBMIX_API_KEY ||
  process.env.MODELSCOPE_API_KEY ||
  process.env.OPENAI_API_KEY
const BASE_URL = normalizeBaseUrl(
  process.env.AI_BASE_URL || process.env.AIHUBMIX_BASE_URL || process.env.MODELSCOPE_BASE_URL || defaultBaseUrl(),
)
const MODEL = process.env.AI_MODEL || process.env.AIHUBMIX_MODEL || process.env.MODELSCOPE_MODEL || defaultModel()

const server = http.createServer(async (req, res) => {
  setCorsHeaders(res)

  if (req.method === 'OPTIONS') {
    res.writeHead(204)
    res.end()
    return
  }

  if (
    req.method !== 'POST' ||
    !['/api/study-suggestion', '/api/validate-plan', '/api/generate-plan'].includes(req.url)
  ) {
    sendJson(res, 404, { error: 'Not found' })
    return
  }

  try {
    if (!API_KEY) {
      sendJson(res, 503, { error: 'AI_API_KEY is not configured.' })
      return
    }

    const requestBody = await readJson(req)
    const messages = buildMessages(req.url, requestBody)

    const response = await requestChatCompletion(messages)

    const data = await response.json()

    if (!response.ok) {
      sendJson(res, response.status, { error: data.error?.message || 'OpenAI request failed.' })
      return
    }

    const outputText = extractOutputText(data)

    if (req.url === '/api/validate-plan') {
      sendJson(res, 200, parseValidationResult(outputText))
      return
    }

    if (req.url === '/api/generate-plan') {
      sendJson(res, 200, parseGeneratedPlanResult(outputText))
      return
    }

    sendJson(res, 200, {
      suggestion: outputText,
      source: `${PROVIDER} ${MODEL}`,
    })
  } catch (error) {
    sendJson(res, 500, { error: error.message || 'Unexpected server error.' })
  }
})

server.listen(PORT, () => {
  console.log(`AI suggestion server running at http://127.0.0.1:${PORT}`)
  console.log(`Provider: ${PROVIDER}`)
  console.log(`Base URL: ${BASE_URL}`)
  console.log(`Model: ${MODEL}`)
})

function setCorsHeaders(res) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
}

function requestChatCompletion(messages) {
  return fetch(`${BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      messages,
      temperature: 0.2,
    }),
  })
}

function buildStudySuggestionMessages(studyContext) {
  return [
    {
      role: 'system',
      content: 'You are a concise study assistant for university students. Give one practical paragraph, under 90 words, based only on the supplied task and resource data.',
    },
    {
      role: 'user',
      content: `Create a focused study suggestion from this JSON:\n${JSON.stringify(studyContext, null, 2)}`,
    },
  ]
}

function buildMessages(url, requestBody) {
  if (url === '/api/validate-plan') return buildPlanValidationMessages(requestBody)
  if (url === '/api/generate-plan') return buildPlanGenerationMessages(requestBody)
  return buildStudySuggestionMessages(requestBody)
}

function buildPlanValidationMessages(planInput) {
  return [
    {
      role: 'system',
      content: [
        'You validate study-planner inputs.',
        'Return strict JSON only, with this shape:',
        '{"valid": boolean, "reason": "short user-facing reason", "cleanedSubject": "string", "cleanedGoal": "string", "minutes": number}',
        'A valid input must have a recognizable study subject, a real available time in minutes, and a goal that looks like a learning task.',
        'Reject random text, jokes, profanity, meaningless repeated characters, and time text without a plausible duration.',
      ].join(' '),
    },
    {
      role: 'user',
      content: JSON.stringify(planInput, null, 2),
    },
  ]
}

function buildPlanGenerationMessages(planInput) {
  return [
    {
      role: 'system',
      content: [
        'You generate concise, practical study plans for university students.',
        'Return strict JSON only, with this shape:',
        '{"valid": boolean, "reason": "short reason", "cleanedSubject": "string", "cleanedGoal": "string", "minutes": number, "summary": "one sentence", "steps": [{"label": "string", "minutes": number, "detail": "string"}]}',
        'A valid input must have a recognizable study subject, a realistic available time from 15 to 360 minutes, and a concrete learning goal.',
        'Reject random text, jokes, profanity, meaningless repeated characters, and time text without a plausible duration.',
        'If valid, create 3 to 5 steps. Make step labels specific to the subject and goal, not generic.',
        'The sum of step minutes should be close to the available minutes.',
        'Use the same language as the user input when it is clearly Chinese; otherwise use English.',
      ].join(' '),
    },
    {
      role: 'user',
      content: JSON.stringify(planInput, null, 2),
    },
  ]
}

function parseValidationResult(outputText) {
  const jsonText = extractJsonObject(outputText)
  const parsed = JSON.parse(jsonText)

  return {
    valid: Boolean(parsed.valid),
    reason: String(parsed.reason || ''),
    cleanedSubject: String(parsed.cleanedSubject || ''),
    cleanedGoal: String(parsed.cleanedGoal || ''),
    minutes: Number(parsed.minutes || 0),
    source: `${PROVIDER} ${MODEL}`,
  }
}

function parseGeneratedPlanResult(outputText) {
  const jsonText = extractJsonObject(outputText)
  const parsed = JSON.parse(jsonText)

  return {
    valid: Boolean(parsed.valid),
    reason: String(parsed.reason || ''),
    cleanedSubject: String(parsed.cleanedSubject || ''),
    cleanedGoal: String(parsed.cleanedGoal || ''),
    minutes: Number(parsed.minutes || 0),
    summary: String(parsed.summary || ''),
    steps: Array.isArray(parsed.steps)
      ? parsed.steps
          .map((step) => ({
            label: String(step.label || '').trim(),
            minutes: Number(step.minutes || 0),
            detail: String(step.detail || '').trim(),
          }))
          .filter((step) => step.label && step.minutes > 0 && step.detail)
      : [],
    source: `${PROVIDER} ${MODEL}`,
  }
}

function extractJsonObject(text) {
  const start = text.indexOf('{')
  const end = text.lastIndexOf('}')

  if (start === -1 || end === -1 || end <= start) {
    throw new Error('AI validation response was not JSON.')
  }

  return text.slice(start, end + 1)
}

function sendJson(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json' })
  res.end(JSON.stringify(body))
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let body = ''

    req.on('data', (chunk) => {
      body += chunk
    })

    req.on('end', () => {
      try {
        resolve(JSON.parse(body || '{}'))
      } catch (error) {
        reject(new Error('Invalid JSON body.'))
      }
    })

    req.on('error', reject)
  })
}

function extractOutputText(data) {
  const content = data.choices?.[0]?.message?.content

  if (Array.isArray(content)) {
    return content
      .map((item) => item.text || item.content || '')
      .join('')
      .trim()
  }

  return String(content || '').trim() || 'No suggestion was returned.'
}

function detectProvider() {
  if (process.env.AIHUBMIX_API_KEY || process.env.AIHUBMIX_BASE_URL) return 'AIHubMix'
  if (process.env.MODELSCOPE_API_KEY || process.env.MODELSCOPE_BASE_URL) return 'ModelScope'
  if (process.env.OPENAI_API_KEY) return 'OpenAI'
  return 'OpenAI-compatible'
}

function defaultBaseUrl() {
  if (PROVIDER === 'AIHubMix') return 'https://aihubmix.com/v1'
  if (PROVIDER === 'ModelScope') return 'https://api-inference.modelscope.cn/v1'
  return 'https://api.openai.com/v1'
}

function defaultModel() {
  if (PROVIDER === 'ModelScope') return 'Qwen/Qwen3-30B-A3B-Instruct-2507'
  return 'gpt-4o-mini'
}

function normalizeBaseUrl(url) {
  return url.replace(/\/+$/, '')
}
