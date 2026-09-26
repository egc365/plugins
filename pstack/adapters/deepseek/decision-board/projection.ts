import { access, readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import type { BoardConfig, BoardSnapshot, Decision, Evidence, LedgerEntry, ProgramRequirement, SourceHealth, Unit, Worker, WorkerBinding } from "./types.ts";

const DECISION_HEADER = ["ts", "phase", "decision", "why", "evidence", "result"] as const;
const UNIT_HEADER = ["id", "track", "state", "branch", "pr", "sha", "brief"] as const;
const LEDGER_HEADER = ["pr", "sha", "verdict", "evidence", "verifier", "ts"] as const;
const ACCEPTANCE = new Set(["accepted", "candidate", "blocked", "unverified", "unresolved"]);
const MAX_WORKERS = 50;
const MAX_ROWS = 500;

function assertRecord(value: unknown, label: string): asserts value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(label + " must be an object");
}
function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.trim() === "") throw new Error(label + " must be a non-empty string");
  return value;
}
function stringArray(value: unknown, label: string): readonly string[] {
  if (!Array.isArray(value) || value.some(item => typeof item !== "string")) throw new Error(label + " must be a string array");
  return value;
}
function parseRequirement(value: unknown, index: number): ProgramRequirement {
  assertRecord(value, "requirements[" + index + "]");
  const status = requiredString(value.status, "requirements[" + index + "].status");
  if (!ACCEPTANCE.has(status)) throw new Error("requirements[" + index + "].status is invalid");
  return { id: requiredString(value.id, "requirement id"), title: requiredString(value.title, "requirement title"), detail: requiredString(value.detail, "requirement detail"), status: status as ProgramRequirement["status"], evidenceIds: stringArray(value.evidenceIds, "requirement evidenceIds"), cardPaths: stringArray(value.cardPaths, "requirement cardPaths") };
}
function parseEvidence(value: unknown, index: number): Evidence {
  assertRecord(value, "evidence[" + index + "]");
  const status = requiredString(value.status, "evidence[" + index + "].status");
  if (!ACCEPTANCE.has(status)) throw new Error("evidence[" + index + "].status is invalid");
  return { id: requiredString(value.id, "evidence id"), label: requiredString(value.label, "evidence label"), sourcePath: requiredString(value.sourcePath, "evidence sourcePath"), scope: requiredString(value.scope, "evidence scope"), status: status as Evidence["status"] };
}
function parseWorker(value: unknown, index: number): WorkerBinding {
  assertRecord(value, "workers[" + index + "]");
  return { role: requiredString(value.role, "worker role"), identity: requiredString(value.identity, "worker identity"), sessionId: requiredString(value.sessionId, "worker sessionId"), card: requiredString(value.card, "worker card"), nextAction: requiredString(value.nextAction, "worker nextAction"), ledgerPath: typeof value.ledgerPath === "string" ? value.ledgerPath : undefined };
}

export function parseConfig(value: unknown): BoardConfig {
  assertRecord(value, "config");
  if (!Array.isArray(value.requirements) || !Array.isArray(value.evidence) || !Array.isArray(value.workers)) throw new Error("requirements, evidence, and workers must be arrays");
  if (value.workers.length > MAX_WORKERS) throw new Error("workers exceeds the bounded limit of 50");
  const refreshSeconds = value.refreshSeconds === undefined ? undefined : Number(value.refreshSeconds);
  if (refreshSeconds !== undefined && !Number.isFinite(refreshSeconds)) throw new Error("refreshSeconds must be numeric");
  const requirements = value.requirements.map(parseRequirement);
  const evidence = value.evidence.map(parseEvidence);
  const workers = value.workers.map(parseWorker);
  const requirementIds = new Set(requirements.map(item => item.id));
  const evidenceIds = new Set(evidence.map(item => item.id));
  if (requirementIds.size !== requirements.length) throw new Error("requirement IDs must be unique");
  if (evidenceIds.size !== evidence.length) throw new Error("evidence IDs must be unique");
  for (const requirement of requirements) for (const id of requirement.evidenceIds) if (!evidenceIds.has(id)) throw new Error("requirement " + requirement.id + " references unknown evidence " + id);
  return { title: requiredString(value.title, "title"), provenanceWarning: typeof value.provenanceWarning === "string" ? value.provenanceWarning : undefined, refreshSeconds, dshOrigin: typeof value.dshOrigin === "string" ? value.dshOrigin : undefined, orchStore: typeof value.orchStore === "string" ? value.orchStore : undefined, decisionsPath: requiredString(value.decisionsPath, "decisionsPath"), legacyStatePath: typeof value.legacyStatePath === "string" ? value.legacyStatePath : undefined, requirements, evidence, workers };
}

async function rpc(origin: string, method: string, payload: object): Promise<unknown> {
  const rpcId = crypto.randomUUID();
  const response = await fetch(new URL("/api/" + method, origin), { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ type: "client-request", rpcId, method, payload }), signal: AbortSignal.timeout(5000) });
  const body = await response.json() as { rpcId?: string; result?: { ok?: boolean; value?: unknown; error?: { message?: string } } };
  if (!response.ok || body.rpcId !== rpcId || body.result?.ok !== true) throw new Error(body.result?.error?.message ?? "native RPC failed");
  return body.result.value;
}

function parseTsv(raw: string, expected: readonly string[], label: string): string[][] {
  const lines = raw.replace(/\r/g, "").split("\n").filter(Boolean);
  if (lines[0] !== expected.join("\t")) throw new Error(label + " has an unexpected header");
  if (lines.length - 1 > MAX_ROWS) throw new Error(label + " exceeds the bounded limit of " + MAX_ROWS + " rows");
  return lines.slice(1).map((line, index) => { const cells = line.split("\t"); if (cells.length !== expected.length) throw new Error(label + " row " + (index + 2) + " has an unexpected column count"); return cells; });
}
async function readDecisions(path: string): Promise<Decision[]> {
  return parseTsv(await readFile(resolve(path), "utf8"), DECISION_HEADER, "decisions.tsv").map(cells => ({ ts: cells[0]!, phase: cells[1]!, decision: cells[2]!, why: cells[3]!, evidence: cells[4]!, result: cells[5]!, sourcePath: path }));
}
async function readOrch(storePath: string): Promise<{ units: Unit[]; ledger: LedgerEntry[] }> {
  const units = parseTsv(await readFile(join(resolve(storePath), "units.tsv"), "utf8"), UNIT_HEADER, "units.tsv").map(c => ({ id: c[0]!, track: c[1]!, state: c[2]!, branch: c[3]!, pr: c[4]!, sha: c[5]!, brief: c[6]! }));
  const verdicts = new Set(["live-ui-verified", "unit-test-verified", "type-check-only", "verifier-blocked", "verifier-failed"]);
  const ledger = parseTsv(await readFile(join(resolve(storePath), "ledger.tsv"), "utf8"), LEDGER_HEADER, "ledger.tsv").map((c, index) => { if (!verdicts.has(c[2]!)) throw new Error("ledger.tsv row " + (index + 2) + " has an invalid verdict"); return { pr: c[0]!, sha: c[1]!, verdict: c[2] as LedgerEntry["verdict"], evidence: c[3]!, verifier: c[4]!, ts: c[5]! }; });
  return { units, ledger };
}
async function terminalStatus(origin: string, sessionId: string): Promise<{ status: "completed" | "error" | "unknown"; detail: string }> {
  const value = await rpc(origin, "session.history", { sessionId, maxMessages: 1 });
  assertRecord(value, "session.history response");
  const events = Array.isArray(value.events) ? value.events : [];
  for (const wrapper of events.slice(-200).reverse()) {
    if (typeof wrapper !== "object" || wrapper === null) continue;
    const event = (wrapper as Record<string, unknown>).event;
    if (typeof event !== "object" || event === null || (event as Record<string, unknown>).type !== "turn/end") continue;
    const data = (event as Record<string, unknown>).data;
    if (typeof data !== "object" || data === null) return { status: "unknown", detail: "Last turn ended without a typed reason" };
    const reason = (data as Record<string, unknown>).reason;
    const kind = typeof reason === "object" && reason !== null ? (reason as Record<string, unknown>).kind : undefined;
    return kind === "completed" ? { status: "completed", detail: "Bounded native history reports the last turn completed" } : { status: "error", detail: "Bounded native history reports terminal outcome: " + String(kind ?? "unknown") };
  }
  return { status: "unknown", detail: "No terminal turn was found in the last 200 returned events" };
}

async function checkBinding(binding: WorkerBinding): Promise<string | null> {
  if (!binding.ledgerPath) return null;
  const value: unknown = JSON.parse(await readFile(resolve(binding.ledgerPath), "utf8"));
  assertRecord(value, "worker ledger");
  if (value.sessionId !== binding.sessionId) throw new Error("worker ledger session does not match configured session");
  if (value.roleId !== binding.identity) throw new Error("worker ledger Roles identity does not match configured identity");
  return binding.ledgerPath;
}
function projectWorker(binding: WorkerBinding, sessions: Map<string, Record<string, unknown>>, observedAt: string): Worker {
  const session = sessions.get(binding.sessionId);
  if (!session) return { ...binding, status: "unknown", observedAt: null, detail: "Configured session was not returned by native session.list", source: "configured-unobserved" };
  const running = session.running === true;
  return { ...binding, status: running ? "running" : "unknown", observedAt, detail: running ? "Native session.list reports running" : "Native session is inactive; checking terminal history", source: "native-session" };
}

export async function buildSnapshot(config: BoardConfig): Promise<BoardSnapshot> {
  const observedAt = new Date().toISOString();
  const health: SourceHealth[] = [];
  let workers: Worker[] = config.workers.map(binding => ({ ...binding, status: "unknown", observedAt: null, detail: "Native session source unavailable", source: "configured-unobserved" }));
  for (const binding of config.workers) {
    try { const path = await checkBinding(binding); if (path) health.push({ source: path, status: "ok", detail: "Role identity and session binding confirmed" }); }
    catch (error) { health.push({ source: binding.ledgerPath ?? binding.sessionId, status: "error", detail: String(error) }); }
  }
  try {
    const value = await rpc(config.dshOrigin ?? "http://127.0.0.1:3080", "session.list", {}); assertRecord(value, "session.list response");
    const items = Array.isArray(value.items) ? value.items : [];
    const sessions = new Map(items.filter(item => typeof item === "object" && item !== null).map(item => [String((item as Record<string, unknown>).sessionId), item as Record<string, unknown>]));
    workers = config.workers.map(binding => projectWorker(binding, sessions, observedAt));
    const stopped = workers.filter(worker => worker.status === "unknown" && worker.source === "native-session");
    if (stopped.length > 12) health.push({ source: "native session.history", status: "stale", detail: "Skipped terminal checks beyond the bounded limit of 12 stopped workers" });
    for (const worker of stopped.slice(0, 12)) {
      try { const terminal = await terminalStatus(config.dshOrigin ?? "http://127.0.0.1:3080", worker.sessionId); workers = workers.map(item => item.sessionId === worker.sessionId ? { ...item, ...terminal } : item); }
      catch (error) { health.push({ source: "native session.history " + worker.sessionId, status: "error", detail: String(error) }); }
    }
    health.push({ source: "native session.list", status: "ok", detail: "Observed " + items.length + " sessions without waking a model" });
  } catch (error) { health.push({ source: "native session.list", status: "error", detail: String(error) }); }
  let decisions: Decision[] = [];
  try { decisions = await readDecisions(config.decisionsPath); health.push({ source: config.decisionsPath, status: "ok", detail: "Loaded " + decisions.length + " decisions" }); }
  catch (error) { health.push({ source: config.decisionsPath, status: "error", detail: String(error) }); }
  let units: Unit[] = []; let ledger: LedgerEntry[] = [];
  if (config.orchStore) {
    try { ({ units, ledger } = await readOrch(config.orchStore)); health.push({ source: config.orchStore, status: "ok", detail: "Loaded " + units.length + " canonical units and " + ledger.length + " verdicts" }); }
    catch (error) { health.push({ source: config.orchStore, status: "error", detail: String(error) }); }
  } else health.push({ source: "orchestration store", status: "stale", detail: "No canonical store configured" });
  const legacyImports: Array<{ label: string; status: "unverified"; sourcePath: string }> = [];
  if (config.legacyStatePath) {
    try { await readFile(resolve(config.legacyStatePath), "utf8"); legacyImports.push({ label: "Legacy state import", status: "unverified", sourcePath: config.legacyStatePath }); health.push({ source: config.legacyStatePath, status: "stale", detail: "Available as a legacy unverified origin only" }); }
    catch (error) { health.push({ source: config.legacyStatePath, status: "error", detail: String(error) }); }
  }
  const readableEvidence = new Set<string>();
  for (const item of config.evidence) {
    try { await access(resolve(item.sourcePath)); readableEvidence.add(item.id); health.push({ source: item.sourcePath, status: item.status === "accepted" ? "ok" : "stale", detail: item.scope }); }
    catch (error) { health.push({ source: item.sourcePath, status: "error", detail: String(error) }); }
  }
  const acceptedEvidence = new Set(config.evidence.filter(item => item.status === "accepted" && readableEvidence.has(item.id)).map(item => item.id));
  const sourcesHealthy = health.every(item => item.status === "ok");
  const overallDone = sourcesHealthy && config.requirements.length > 0 && config.requirements.every(item => item.status === "accepted" && item.evidenceIds.length > 0 && item.evidenceIds.every(id => acceptedEvidence.has(id)));
  const buildLoopActive = health.every(item => item.status !== "error") && workers.some(worker => worker.status === "running");
  return { title: config.title, provenanceWarning: config.provenanceWarning ?? "Configured and recovered sources may not contain the full early decision history.", observedAt, refreshSeconds: Math.max(5, Math.min(config.refreshSeconds ?? 15, 300)), buildLoopActive, overallDone, requirements: config.requirements, evidence: config.evidence, workers, units, ledger, decisions, legacyImports, health };
}
