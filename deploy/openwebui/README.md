# Deploying QMS Auditor ISO 9001:2026 on OpenWebUI

This sets up the **Full gateway** deployment: OpenWebUI as the chat UI,
Ollama for local inference, and an [OpenWebUI Pipelines](https://github.com/open-webui/pipelines)
container running `pipelines/qms_auditor_gateway_filter.py`, which shells out
to this skill's real Python gate scripts (`scope_gate.py`,
`preflight_request_guard.py`, `harness_gate_executor.py`) on every chat turn.

```
                 ┌───────────────┐
   browser  ───▶ │   OpenWebUI    │
                 └───────┬────────┘
                         │ OpenAI-compatible connection
                         ▼
                 ┌───────────────┐        inlet(): scope_gate,
                 │   Pipelines    │  ◀──── preflight_request_guard
                 │ (gateway       │
                 │  filter)       │  ────▶ outlet(): harness_gate_executor
                 └───────┬────────┘
                         │ forwards generation
                         ▼
                 ┌───────────────┐
                 │    Ollama      │
                 └───────────────┘
```

## 0. Prerequisites

- Docker + Docker Compose
- Your own licensed copies of the ISO PDFs placed under `assets/standards/`
  (see the root `README.md` — these are gitignored and never leave your
  machine)

## 1. Start the stack

From the repository root:

```bash
cp .env.example .env      # change PIPELINES_API_KEY before exposing beyond localhost
docker compose up -d
docker compose logs -f pipelines   # confirm "QMS Auditor ISO 9001:2026 Gateway" loaded
```

Pull an Ollama model (CPU-friendly example; swap for whatever you run):

```bash
docker compose exec ollama ollama pull qwen2.5:14b-instruct
```

## 2. Connect OpenWebUI to the Pipelines gateway

1. Open http://localhost:3000 and finish the first-run admin signup.
2. Go to **Admin Panel → Settings → Connections**.
3. Under **OpenAI API**, add a connection:
   - URL: `http://pipelines:9099` (already wired via `OPENAI_API_BASE_URLS`
     in `docker-compose.yml` — this step confirms it, or edit the key)
   - Key: the value of `PIPELINES_API_KEY` from your `.env`
4. Go to **Admin Panel → Settings → Pipelines**. You should see
   **QMS Auditor ISO 9001:2026 Gateway** listed (loaded from
   `deploy/openwebui/pipelines/qms_auditor_gateway_filter.py`). Open it and
   set the **Valves**:
   - `SKILL_ROOT` → `/app/qms-skill` (matches the compose volume mount —
     leave as-is unless you changed the mount path)
   - `PYTHON_BIN` → `python3`
   - Toggle `BLOCK_ON_OUT_OF_SCOPE` / `BLOCK_ON_AMBIGUOUS` /
     `BLOCK_ON_GUARDRAIL` / `VALIDATE_GATE_TRACE_ON_OUTLET` as needed
     (all default to on)

## 3. Create the Model preset

1. **Admin Panel → Settings → Models** → create a new model, e.g.
   `qms-auditor-iso9001-2026`, backed by the Ollama model you pulled.
2. Under that model's **Pipelines** tab, enable
   **QMS Auditor ISO 9001:2026 Gateway** (the `pipelines` valve list
   defaults to `["*"]`, so it already applies to every model — narrow it to
   this specific model ID once you're past initial testing).
3. Leave the model's own system prompt empty or minimal — the gateway
   injects the condensed governance header (`pipelines/system_prompt.md`)
   on every turn via `inlet()`.

## 4. Load the reference material as Knowledge (RAG)

The gateway filter injects a *condensed* governance header only (a few KB) —
it deliberately does not paste all of `SKILL.md` and `references/` into
every request, since that would blow the context budget on a local model.
For the model to actually cite clause text and reference rules, load the
real reference corpus into OpenWebUI's RAG:

1. **Workspace → Knowledge → Create a knowledge base**, e.g.
   `qms-iso9001-2026-references`.
2. Upload:
   - every file under `references/` (markdown — clause rules, evidence
     schema, NC classification, etc.)
   - `assets/templates/*.md` (report/checklist templates)
   - your locally-placed ISO PDFs under `assets/standards/` **only if this
     Knowledge base stays private to this deployment** — see the licensing
     warning in the root `README.md` / `NOTICE.md`.
3. Attach this Knowledge base to the `qms-auditor-iso9001-2026` model
   (**Models → your model → Knowledge**).

## 5. Try it

Ask the model something in scope, e.g. (Thai or English):

> ตรวจสอบ clause 8.5.1 — องค์กรมี work instruction แต่ไม่มีบันทึกการตรวจสอบ

The pipeline should:
- Pass `scope_gate` / `preflight_request_guard` silently (visible in
  `docker compose logs pipelines` if you add debug prints)
- Let the model answer using the injected governance header + your
  Knowledge base citations
- (L7: the harness also enforces the Conditional Qualifier Gate on that trace — `references/42` Part 9.)
- If the model returns a structured `gate_execution_trace` verdict block,
  `outlet()` runs it through `harness_gate_executor.py` and appends a
  rejection banner if the trace is internally inconsistent

Then try an out-of-scope prompt, e.g. "help me with ISO 27001 gap analysis"
— it should be blocked before reaching the model, with the Thai
out-of-scope dialog from `scripts/scope_gate.py`.

## Notes / limitations of this MVP gateway

- The filter calls the *top-level* deterministic scripts (scope gate,
  preflight guard, harness gate executor). It does **not** yet call the
  executable Audit World Model (`scripts/awm_runtime`, the FastAPI package
  for `predictive_audit_assistance`) — that requires running it as its own
  service (see `scripts/awm_runtime/README.md`) and adding a second
  Pipelines integration if you need that route.
- `closed_source_entrypoint.py --validate-sources` (manifest/RAG-policy
  validation) is not run on every turn to keep latency down; run it
  manually after editing `assets/manifests/*.json`:
  ```bash
  python scripts/closed_source_entrypoint.py --request "healthcheck" --validate-sources
  ```
- This is a gate/scope/harness wrapper, not a full reproduction of every
  BLOCK in `SKILL.md` (e.g. the org-branded MASCI report renderer,
  `scripts/org_report_renderer.js`, still needs to be run out-of-band on the
  model's structured output — it is not wired into the pipeline).
