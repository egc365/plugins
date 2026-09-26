# Native Benny for Roles

This adapter installs Benny as a native Roles agent. It uses the existing `poteto-agent` preset and the exact `openai-codex/gpt-5.6-sol` route. It does not install another scheduler or claim that Slack and Cursor automations ran.

## Activate Benny

Root copies `deployment.example.json` to a deployment-owned path and fills the registered Development workspace ID and one exact session ID from that workspace.

Verify discovery without changing Roles state:

```sh
node pstack/adapters/deepseek/benny/activate.mjs verify /absolute/path/benny-deployment.json
```

Create one Benny role, start its native session, preview the first task, and submit that task:

```sh
node pstack/adapters/deepseek/benny/activate.mjs activate /absolute/path/benny-deployment.json --submit
```

Without `--submit`, activation stops after the durable Roles preview. Repeating the command reuses an exact matching Benny role and prepared task. It refuses a conflicting role, an unavailable preset or route, and uncertain native start receipts.

## Operational sources

`ROLE.md` adapts direct Roles tasks to the preserved upstream Benny workflow. `upstream.manifest.json` pins all 12 copied files by SHA-256. `activate.mjs` verifies every hash before it reads or changes Roles state.

The first task consumes `work/cordis-goal/install-review-result.md` and `work/cordis-goal/studio-install-receipt.json`. It does not repeat the finished phase and Studio review or the independent work in `/wiki/001-planning`.

## Check the adapter

```sh
npm run check
python3 /wiki/2026-09-24/https-claude-ai-code-session-012zpiqywbajqpmmw6rqb29g/work/cordis-script-index/integrations/deterministic-repair/src/script_index.py check --root . --manifest script-index.manifest.json --inventory script-index.inventory.json --workbook script-index.xlsx
```
