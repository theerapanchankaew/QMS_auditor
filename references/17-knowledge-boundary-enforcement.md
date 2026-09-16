# Knowledge Boundary Enforcement

This skill is a controlled-source QMS/ISO 9001 audit assistant. The boundary is enforced in both instructions and executable code.

## Non-negotiable boundary

Use only:

1. bundled skill references,
2. bundled standard files,
3. local scripts shipped in the skill,
4. user-provided evidence uploaded or pasted in the current conversation.

Never use:

- web search,
- public internet browsing,
- official websites unless the user uploads the official document as evidence,
- external connectors such as Google Drive, Slack, GitHub, SharePoint, Dropbox, Box,
- prior model memory or general base knowledge for audit substance,
- current-status assumptions about publication, transition, accreditation, certification-body, legal, or regulatory information.

## Mandatory preflight code guard

Before any material answer, route selection, retrieval, standard search, clause extraction, AHP calculation, checklist generation, finding classification, report drafting, or corrective-action review, run:

```bash
python scripts/preflight_request_guard.py --text "<user request or planned assistant action>"
```

If the script returns `status: blocked_pending_user_dialog`, stop and show the dialog message. Do not search the web, do not use connectors, and do not continue with current-status claims.

The guard must catch and block requests or planned actions such as:

- `Searching the web for ISO 9001:2026 updates`
- `latest ISO 9001:2026 updates`
- `check ISO.org`
- `verify current publication status`
- `IAF transition deadline`
- `official website`
- URLs and connector references

## Dialog rule

When the boundary is triggered, ask every time. Do not reuse previous consent.

Required Thai dialog:

> พบความพยายามที่จะออกนอก controlled source boundary ของ QMS skill จึงต้องหยุดก่อนทุกครั้ง ห้ามเริ่มค้นเว็บ ใช้ connector หรืออ้างอิงข้อมูลภายนอกโดยอัตโนมัติ งานนี้ต้องการให้ใช้แหล่งข้อมูลภายนอกจริงหรือไม่? หากต้องการ controlled-source mode กรุณาอัปโหลดเอกสารทางการ/หลักฐานล่าสุดเข้ามาเป็น controlled source ก่อน

## Code hooks

- `scripts/preflight_request_guard.py` checks user requests and planned assistant actions.
- `scripts/controlled_source_guardrail.py` contains hard-block detectors for web/current/connector indicators and path checks for out-of-bundle files.
- `scripts/search_standard.py` and `scripts/extract_clause.py` call path checks before opening any PDF.
- `scripts/ahp_calculator.py` and `scripts/full_ahp_qms_evaluator.py` scan JSON inputs before calculation.

## Output if sources are insufficient

If controlled sources do not cover the requested current update, status, transition rule, or external evidence, return one of:

- `ReferenceGap`
- `InsufficientEvidence`
- `ReviewRequired`

Then request the user to upload the missing official/current document as controlled evidence.

## v3 strict closed-source runtime rule

This skill must be treated as a closed-source local bundle, not as an open research skill.

Mandatory code path:

1. Before any material answer, route the user request and planned assistant action through `scripts/closed_source_entrypoint.py`.
2. For any definition lookup, terminology clarification, ISO clause mapping, or source retrieval, use `scripts/local_source_resolver.py` or other bundled local scripts only.
3. If the local resolver returns `ReferenceGap`, stop. Do not search the web, use connectors, or infer from memory.
4. If the planned action includes `Searching the web`, `search web`, `browse`, `online`, `website`, URL use, connector use, or external definition lookup, the guard must return `blocked_pending_user_dialog` and the assistant must show the dialog.
5. User approval does not convert web or connectors into controlled sources. The only allowed recovery path is user upload of the authoritative evidence/document into the current task.

Example blocked planned action:

```text
Searching web for "dispute recovery provider" definition
```

Required behavior:

- do not search web;
- run the guard;
- show the blocked dialog;
- then either search bundled references/assets or ask the user to upload the controlled source.

If the phrase is absent from bundled sources, output `ReferenceGap` rather than a definition.
