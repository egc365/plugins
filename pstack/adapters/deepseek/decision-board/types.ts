export type Acceptance = "accepted" | "candidate" | "blocked" | "unverified" | "unresolved";
export type WorkerStatus = "running" | "error" | "completed" | "unknown";
export type Verdict = "live-ui-verified" | "unit-test-verified" | "type-check-only" | "verifier-blocked" | "verifier-failed";

export interface Evidence { readonly id: string; readonly label: string; readonly sourcePath: string; readonly scope: string; readonly status: Acceptance }
export interface ProgramRequirement { readonly id: string; readonly title: string; readonly detail: string; readonly status: Acceptance; readonly evidenceIds: readonly string[]; readonly cardPaths: readonly string[] }
export interface WorkerBinding { readonly role: string; readonly identity: string; readonly sessionId: string; readonly card: string; readonly nextAction: string; readonly ledgerPath?: string }
export interface Worker extends WorkerBinding { readonly status: WorkerStatus; readonly observedAt: string | null; readonly detail: string; readonly source: "native-session" | "configured-unobserved" }
export interface Decision { readonly ts: string; readonly phase: string; readonly decision: string; readonly why: string; readonly evidence: string; readonly result: string; readonly sourcePath: string }
export interface Unit { readonly id: string; readonly track: string; readonly state: string; readonly branch: string; readonly pr: string; readonly sha: string; readonly brief: string }
export interface LedgerEntry { readonly pr: string; readonly sha: string; readonly verdict: Verdict; readonly evidence: string; readonly verifier: string; readonly ts: string }
export interface SourceHealth { readonly source: string; readonly status: "ok" | "error" | "stale"; readonly detail: string }
export interface BoardConfig { readonly title: string; readonly provenanceWarning?: string; readonly refreshSeconds?: number; readonly dshOrigin?: string; readonly orchStore?: string; readonly decisionsPath: string; readonly legacyStatePath?: string; readonly requirements: readonly ProgramRequirement[]; readonly evidence: readonly Evidence[]; readonly workers: readonly WorkerBinding[] }
export interface BoardSnapshot { readonly title: string; readonly provenanceWarning: string; readonly observedAt: string; readonly refreshSeconds: number; readonly buildLoopActive: boolean; readonly overallDone: boolean; readonly requirements: readonly ProgramRequirement[]; readonly evidence: readonly Evidence[]; readonly workers: readonly Worker[]; readonly units: readonly Unit[]; readonly ledger: readonly LedgerEntry[]; readonly decisions: readonly Decision[]; readonly legacyImports: readonly { label: string; status: "unverified"; sourcePath: string }[]; readonly health: readonly SourceHealth[] }
