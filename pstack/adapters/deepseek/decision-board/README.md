# DeepSeek decision board

A local, read-only projection of the P-Stack program record. It combines the existing orchestration store, Show Me Your Work log, configured Roles bindings, native DSH session observations, and scoped evidence pointers. It does not schedule agents, modify the store, or wake models.

## Run

Use Node.js 24 or newer. Keep deployment configuration outside tracked source.

```sh
cd pstack/adapters/deepseek/decision-board
node server.ts --config /absolute/path/to/board-config.json --port 0
```

The command prints the selected ephemeral localhost URL. Open that exact URL. The board refreshes every 5–300 seconds and has a manual refresh button.

Start from `config.example.json`. Point `orchStore` at an existing store containing canonical `units.tsv` and `ledger.tsv`. Point `decisionsPath` at the canonical six-column log with `ts/phase/decision/why/evidence/result`. Worker entries bind an exact Roles role ID to one native session; an optional ledger path is checked but its headers and raw content are never returned to the browser. `legacyStatePath` is displayed only as an unverified import.

## Status rules

- A running worker comes only from native `session.list` at the current observation time.
- A stopped worker becomes completed or error only from its last `turn/end` reason in native `session.history`. At most 12 stopped workers are checked per refresh and only the final 200 returned events are inspected.
- Inactive without a terminal event remains unknown. Worker completion does not accept a requirement.
- `BUILD LOOP ACTIVE` requires at least one observed running configured worker and no source errors.
- Overall acceptance requires every requirement and its linked, readable evidence to be accepted, with every source healthy. Candidate, blocked, unverified, unresolved, stale, and error remain distinct.
- An evidence row describes its verification scope. Artifact existence can therefore remain separate from requirement acceptance.

## Verify

```sh
npm run check
```

The script inventory is independently enumerated in `script-index.manifest.json`; `script-index.inventory.json` is canonical machine-readable extraction and `script-index.xlsx` is its derived workbook.

## Boundaries

The server binds only to `127.0.0.1` and defaults to port `0`. It makes bounded, read-only native requests. It serves only fixed files from `public/`, does not expose unrestricted files or ledger headers, and carries no credentials. Root owns launch and any live integration.
