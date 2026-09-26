import assert from 'node:assert/strict'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { parseDeployment, run, verifyUpstream } from './activate.mjs'

const deployment = { version: 1, origin: 'http://127.0.0.1:3080', workspaceId: 'workspace-1', contextSessionId: 'session-context', role: { name: 'Benny', provider: 'openai-codex', model: 'gpt-5.6-sol', agentPreset: 'poteto-agent' } }

function response(value, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { 'content-type': 'application/json' } })
}

function native() {
  const board = { roles: [], starts: [], tasks: [], prepared: [], submissions: [] }
  const operations = []
  const request = async (_url, init = {}) => {
    assert.equal(init.headers.origin, 'http://127.0.0.1:3080')
    assert.equal(init.headers['x-session-workspace-id'], 'workspace-1')
    assert.equal(init.headers['x-session-workspace-session'], 'session-context')
    if (!init.method) return response({ workspace: { id: 'workspace-1', cwd: '/workspace' } })
    const operation = JSON.parse(init.body)
    operations.push(operation.kind)
    if (operation.kind === 'presets') return response({ ok: true, value: { presets: [{ id: 'poteto-agent', broken: false }] } })
    if (operation.kind === 'catalog-context') return response({ ok: true, value: { catalog: { groups: [{ id: 'openai-codex', models: [{ id: 'gpt-5.6-sol' }] }] } } })
    if (operation.kind === 'read') return response({ ok: true, value: structuredClone(board) })
    if (operation.kind === 'add-role') {
      board.roles.push({ id: 'role-benny', revision: 1, config: operation.config })
      return response({ ok: true, value: structuredClone(board) })
    }
    if (operation.kind === 'start') {
      const role = board.roles[0]
      role.binding = { sessionId: 'session-benny', origin: 'started', cwd: '/workspace', agentPreset: 'poteto-agent', boundAt: 1 }
      role.revision = 2
      return response({ ok: true, value: { id: operation.requestId, roleId: role.id, roleRevision: 1, sessionId: 'session-benny', config: role.config, state: 'bound' } })
    }
    if (operation.kind === 'select-model') return response({ ok: true, value: { rpcId: 'rpc-select' } })
    if (operation.kind === 'prepare') {
      const prepared = { id: 'prepared-1', roleId: operation.roleId, roleRevision: operation.revision, config: operation.draft, sessionId: 'session-benny', task: operation.task, mode: 'queue', prompt: operation.draft.instructions + '\n\n' + operation.task.instruction, createdAt: 1 }
      board.prepared.push(prepared)
      return response({ ok: true, value: prepared })
    }
    if (operation.kind === 'submit') {
      const prepared = board.prepared.find(item => item.id === operation.preparedId)
      const receipt = { ...prepared, status: 'accepted-queue', sentAt: 2 }
      board.tasks.push(prepared.task)
      board.submissions.push(receipt)
      return response({ ok: true, value: receipt })
    }
    return response({ ok: false, error: 'unexpected operation ' + operation.kind }, 400)
  }
  return { request, operations, board }
}

test('rejects placeholder deployment identities', () => {
  assert.throws(() => parseDeployment({ ...deployment, workspaceId: '<registered-workspace-id>' }), /placeholder/)
})

test('verifies every preserved upstream Benny file', async () => {
  assert.equal(await verifyUpstream(), 12)
})

test('verifies the exact preset and model without mutation', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'benny-test-'))
  const path = join(dir, 'deployment.json')
  await writeFile(path, JSON.stringify(deployment))
  const fake = native()
  try {
    const result = await run('verify', path, { fetch: fake.request })
    assert.deepEqual(result, { status: 'verified', workspace: { id: 'workspace-1', cwd: '/workspace' }, preset: 'poteto-agent', route: 'openai-codex/gpt-5.6-sol', upstreamFiles: 12 })
    assert.deepEqual(fake.operations, ['presets', 'catalog-context'])
  } finally { await rm(dir, { recursive: true, force: true }) }
})

test('creates one native Benny role and previews the corrected first task', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'benny-test-'))
  const path = join(dir, 'deployment.json')
  await writeFile(path, JSON.stringify(deployment))
  const fake = native()
  try {
    const result = await run('activate', path, { fetch: fake.request })
    assert.equal(result.status, 'prepared')
    assert.equal(result.submitted, false)
    assert.equal(fake.board.roles.length, 1)
    assert.equal(fake.board.prepared.length, 1)
    assert.ok(fake.board.roles[0].config.instructions.includes('reproduce-and-fix-issues/SKILL.md'))
    assert.ok(fake.board.prepared[0].task.instruction.includes('session-a12e1f6f-5f67-45aa-a45f-7f2e59286209'))
    assert.ok(fake.board.prepared[0].task.instruction.includes('Do not repeat that review.'))
    assert.equal(fake.operations.includes('submit'), false)
    const submitted = await run('activate', path, { fetch: fake.request, submit: true })
    assert.equal(submitted.status, 'accepted-queue')
    assert.equal(fake.board.roles.length, 1)
    assert.equal(fake.board.submissions.length, 1)
  } finally { await rm(dir, { recursive: true, force: true }) }
})
