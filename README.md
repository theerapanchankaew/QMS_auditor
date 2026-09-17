# QMS Auditor ISO 9001:2026 — Local AI Deployment (OpenWebUI + Ollama)

This repository packages the **QMS Auditor ISO 9001:2026** skill — a governed audit
reasoning system (SKILL.md governance blocks, deterministic gate scripts, ISO
clause references, and an executable Audit World Model runtime) — for deployment
as a **local, private AI assistant** fronted by [OpenWebUI](https://github.com/open-webui/open-webui)
and [Ollama](https://ollama.com).

This is **not** a plain chatbot system prompt. The value of this skill is the
deterministic gate layer (`scripts/scope_gate.py`, `preflight_request_guard.py`,
`closed_source_entrypoint.py`, `harness_gate_executor.py`, …) that enforces
scope, closed-source retrieval, and evidence/severity rules *before and after*
the LLM speaks. The deployment in this repo runs those gates as a real
**OpenWebUI Pipeline (filter)**, not just prompt text — see
[`deploy/openwebui/`](deploy/openwebui/).

## Repository layout

```
SKILL.md               Governance + routing + cognition engine (loaded as system context)
agents/openai.yaml      Display metadata for chat-platform skill registries
references/             60+ clause/rule/governance reference docs (RAG source)
scripts/                48 deterministic gate/validator scripts (stdlib only)
scripts/awm_runtime/    Executable Audit World Model v0.7 (FastAPI package, optional)
assets/standards/       ISO source PDFs — GITIGNORED, see "Licensed standards" below
assets/requirement_profiles/  AtomicRequirement corpus, 65 clauses/155 elements — AI-drafted, unreviewed
assets/templates/       Report/schema/regression templates
assets/tests/           Regression + gate test fixtures
deploy/openwebui/       OpenWebUI Pipeline filter + setup guide (this deployment)
docs/                   Maintainer/architecture docs (not loaded at runtime)
docker-compose.yml       Ollama + OpenWebUI + Pipelines stack
```

## ⚠️ Licensed standards — do not commit

`assets/standards/*.pdf` (ISO 9001:2026 — bundled as an FDIS-stage text
file, content sample-verified against the published Sixth edition; ISO
FDIS 9000:2026, not confirmed published; ISO 9000 glossary) are
**copyrighted ISO/IEC works**, not open content. They are
excluded via `.gitignore`. Before running anything that calls
`scripts/extract_clause.py` or the standard-lookup path:

1. Obtain your own licensed copies of these PDFs.
2. Place them at the exact paths already referenced in `SKILL.md` BLOCK 4:
   - `assets/standards/ISO_FDIS_9001_2026_en.pdf`
   - `assets/standards/ISO_FDIS_9000_2026_en.pdf`
   - `assets/standards/ISO9000GlossaryENv5FA2025.pdf`
   - `assets/standards/ISO_9001_2026_IS_en_scanned.pdf` — the published
     standard (Sixth edition, 2026-09), used only to spot-check the FDIS
     text is still current; it has no text layer, so
     `scripts/extract_clause.py` still runs against the FDIS PDF above, not
     this one (see `assets/requirement_profiles/README.md`).

Never push these files to GitHub, and never let a public Knowledge base in
OpenWebUI expose their raw text to other users.

## Two ways to run this

| Mode | What it uses | When to use |
|---|---|---|
| **Full gateway** (recommended, this repo's default) | OpenWebUI Pipelines filter running the real Python gate scripts + Ollama for generation | You want the scope/preflight/harness gates enforced, not just described in a prompt |
| **Lite** | SKILL.md pasted as a custom Model's system prompt + `references/**` uploaded to OpenWebUI Knowledge for RAG | Quick trial only — the Python gates do **not** run; the model can silently skip them |

This repo implements **Full gateway**. See [`deploy/openwebui/README.md`](deploy/openwebui/README.md)
for the complete setup (docker compose, pipeline install, Knowledge upload,
Model preset).

## Quick start

```bash
# 1. Place your licensed ISO PDFs under assets/standards/ (see above)
# 2. Start the stack
docker compose up -d
# 3. Pull a model into Ollama (once)
docker compose exec ollama ollama pull qwen2.5:14b-instruct
```

Then open OpenWebUI at http://localhost:3000 and follow
[`deploy/openwebui/README.md`](deploy/openwebui/README.md) to enable the
gateway pipeline and load the reference Knowledge base.

## Publishing to GitHub

This repo is intended to stay **private**:
- `assets/standards/*.pdf` are copyrighted ISO drafts (see above).
- `references/43-org-template-contract.md` and `assets/templates/masci-*`
  encode a specific certification body's (MASCI) report branding/format —
  treat as that organization's IP, not for public redistribution.

```bash
git init
git add .
git commit -m "Initial commit: QMS Auditor ISO 9001:2026 skill + OpenWebUI gateway"
# Create the GitHub repo as PRIVATE first (web UI or `gh repo create --private`),
# then:
git remote add origin git@github.com:<your-user>/qms-auditor-iso-9001-2026.git
git branch -M main
git push -u origin main
```

## Deterministic gate quick reference

```bash
python scripts/scope_gate.py --text "<user request>"
python scripts/preflight_request_guard.py --text "<user request>"
python scripts/closed_source_entrypoint.py --request "<user request>" --planned-action "<action>"
python scripts/harness_gate_executor.py --input model_output.json
python scripts/run_regression_suite.py --skill-root . --outdir regression_results
```

See `SKILL.md` for the full route map, cognition engine (25 rules), and
reference index.
