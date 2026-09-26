import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(fileURLToPath(import.meta.url))
const expectedRoute = Object.freeze({ provider: 'openai-codex', model: 'gpt-5.6-sol', agentPreset: 'poteto-agent' })

function record(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(label + ' must be an object')
  return value
}

function text(value, label) {
  if (typeof value !== 'string' || !value.trim() || value.includes('\0') || /^<.*>$/.test(value)) throw new Error(label + ' is missing or still a placeholder')
  return value
}

export function parseDeployment(value) {
  const input = record(value, 'deployment config')
  const role = record(input.role, 'role')
  if (input.version !== 1) throw new Error('deployment config version must be 1')
  const parsed = {
    version: 1,
    origin: text(input.origin, 'origin'),
    workspaceId: text(input.workspaceId, 'workspaceId'),
    contextSessionId: text(input.contextSessionId, 'contextSessionId'),
    role: {
      name: text(role.name, 'role.name'),
      provider: text(role.provider, 'role.provider'),
      model: text(role.model, 'role.model'),
      agentPreset: text(role.agentPreset, 'role.agentPreset')
    }
  }
  const url = new URL(parsed.origin)
  if (url.origin !== parsed.origin || url.protocol !== 'http:' || !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)) throw new Error('origin must be an explicit loopback HTTP origin')
  if (parsed.role.name !== 'Benny') throw new Error('role.name must be Benny')
  for (const key of Object.keys(expectedRoute)) if (parsed.role[key] !== expectedRoute[key]) throw new Error('unsupported Benny ' + key + ': expected ' + expectedRoute[key])
  return parsed
}

async function json(path) {
  return JSON.parse(await readFile(path, 'utf8'))
}

export async function verifyUpstream() {
  const manifest = record(await json(join(root, 'upstream.manifest.json')), 'upstream manifest')
  if (manifest.version !== 1 || !Array.isArray(manifest.files) || manifest.files.length === 0) throw new Error('invalid upstream manifest')
  for (const item of manifest.files) {
    record(item, 'upstream file')
    const path = text(item.path, 'upstream path')
    if (path.startsWith('/') || path.split('/').includes('..')) throw new Error('unsafe upstream path: ' + path)
    const digest = createHash('sha256').update(await readFile(join(root, 'upstream', path))).digest('hex')
    if (digest !== item.sha256) throw new Error('upstream hash mismatch: ' + path)
  }
  return manifest.files.length
}

async function roleConfig(deployment) {
  const instructions = (await readFile(join(root, 'ROLE.md'), 'utf8')).replaceAll('{{BENNY_ROOT}}', root)
  if (instructions.includes('{{BENNY_ROOT}}')) throw new Error('unresolved Benny root placeholder')
  return { ...deployment.role, instructions }
}

async function firstTask(roleId) {
  const config = record(await json(join(root, 'task.config.json')), 'task config')
  if (config.version !== 1 || !Array.isArray(config.inputs) || !Array.isArray(config.observedTests)) throw new Error('invalid task config')
  return {
    id: text(config.id, 'task id'),
    roleId,
    title: text(config.title, 'task title'),
    instruction: await readFile(join(root, text(config.instructionFile, 'instructionFile')), 'utf8'),
    inputs: config.inputs.map((value, index) => text(value, 'task input ' + index)),
    deliverable: text(config.deliverable, 'task deliverable'),
    observedTests: config.observedTests.map((value, index) => text(value, 'observed test ' + index)),
    review: 'unreviewed'
  }
}

function sameRole(a, b) {
  return a.name === b.name && a.provider === b.provider && a.model === b.model && a.agentPreset === b.agentPreset && a.instructions === b.instructions
}

function headers(deployment) {
  return {
    'content-type': 'application/json',
    origin: deployment.origin,
    'x-session-workspace': '1',
    'x-session-workspace-id': deployment.workspaceId,
    'x-session-workspace-session': deployment.contextSessionId
  }
}

function client(deployment, request) {
  const route = deployment.origin + '/session-workspace/operations'
  const common = { headers: headers(deployment), cache: 'no-store' }
  return {
    async workspace() {
      const response = await request(route, common)
      const data = await response.json()
      if (!response.ok || !data.workspace) throw new Error(data.error || 'Roles workspace lookup failed (' + response.status + ')')
      return data.workspace
    },
    async execute(workspace, operation) {
      const response = await request(route, { ...common, method: 'POST', body: JSON.stringify({ ...operation, workspace }) })
      const data = await response.json()
      if (!response.ok || !data.ok || data.value === undefined) throw new Error(data.error || 'Roles operation failed (' + response.status + ')')
      return data.value
    }
  }
}

function catalogHas(catalog, provider, model) {
  return Array.isArray(catalog?.groups) && catalog.groups.some(group => group.id === provider && Array.isArray(group.models) && group.models.some(item => item.id === model))
}

export async function run(command, configPath, options = {}) {
  if (!['verify', 'activate'].includes(command)) throw new Error('command must be verify or activate')
  const deployment = parseDeployment(await json(resolve(configPath)))
  const upstreamFiles = await verifyUpstream()
  const config = await roleConfig(deployment)
  const api = client(deployment, options.fetch ?? fetch)
  const workspace = await api.workspace()
  if (workspace.id !== deployment.workspaceId) throw new Error('Roles returned a different workspace ID')
  const presets = await api.execute(workspace, { kind: 'presets' })
  const preset = presets.presets?.find(item => item.id === config.agentPreset)
  if (!preset || preset.broken) throw new Error('poteto-agent preset is unavailable or broken')
  const catalogResult = await api.execute(workspace, { kind: 'catalog-context', sessionId: deployment.contextSessionId })
  if (!catalogHas(catalogResult.catalog, config.provider, config.model)) throw new Error('openai-codex gpt-5.6-sol is unavailable in the exact native catalog')
  if (command === 'verify') return { status: 'verified', workspace, preset: preset.id, route: config.provider + '/' + config.model, upstreamFiles }

  let board = await api.execute(workspace, { kind: 'read' })
  let matches = board.roles.filter(item => item.config.name === config.name)
  if (matches.length > 1) throw new Error('more than one Benny role exists; reconcile ownership before activation')
  if (matches.length === 0) {
    board = await api.execute(workspace, { kind: 'add-role', config })
    matches = board.roles.filter(item => item.config.name === config.name)
  }
  let role = matches[0]
  if (!role || !sameRole(role.config, config)) throw new Error('existing Benny role differs from the reviewed config; no implicit overwrite')
  if (!role.binding) {
    const requestId = 'benny-' + createHash('sha256').update(workspace.id + '\0' + JSON.stringify(config)).digest('hex').slice(0, 24)
    const start = await api.execute(workspace, { kind: 'start', roleId: role.id, revision: role.revision, requestId })
    if (start.state !== 'bound') throw new Error('native Benny start is ' + start.state + ': ' + (start.error || 'inspect the exact receipt'))
    board = await api.execute(workspace, { kind: 'read' })
    role = board.roles.find(item => item.id === role.id)
  }
  if (!role?.binding) throw new Error('Benny role is not bound to a native session')
  await api.execute(workspace, { kind: 'select-model', roleId: role.id, revision: role.revision })
  board = await api.execute(workspace, { kind: 'read' })
  role = board.roles.find(item => item.id === role.id)
  const task = await firstTask(role.id)
  const submitted = board.submissions.find(item => item.task.id === task.id)
  if (submitted) return { status: submitted.status, roleId: role.id, sessionId: role.binding.sessionId, taskId: task.id, preparedId: submitted.id, submitted: true }
  let prepared = board.prepared.find(item => item.task.id === task.id)
  if (!prepared) prepared = await api.execute(workspace, { kind: 'prepare', roleId: role.id, revision: role.revision, draft: config, mode: 'queue', task })
  if (!options.submit) return { status: 'prepared', roleId: role.id, sessionId: role.binding.sessionId, taskId: task.id, preparedId: prepared.id, submitted: false }
  const receipt = await api.execute(workspace, { kind: 'submit', preparedId: prepared.id, draft: config })
  return { status: receipt.status, roleId: role.id, sessionId: role.binding.sessionId, taskId: task.id, preparedId: prepared.id, submitted: true }
}

async function main() {
  const [command, configPath, ...flags] = process.argv.slice(2)
  if (!command || !configPath || flags.some(flag => flag !== '--submit')) throw new Error('usage: node activate.mjs <verify|activate> <deployment-config.json> [--submit]')
  const result = await run(command, configPath, { submit: flags.includes('--submit') })
  process.stdout.write(JSON.stringify(result, null, 2) + '\n')
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(error => { console.error(error instanceof Error ? error.message : String(error)); process.exitCode = 1 })
