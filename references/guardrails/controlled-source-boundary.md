# Controlled Source Boundary

The QMS skill is closed-source. It can only use:

1. Bundled references and assets in the skill package.
2. User-uploaded controlled evidence explicitly supplied for the current task.
3. Approved local RAG indexes whose source documents are registered in the manifest.

It must not use web search, connectors, browsing, current-status checks, official websites, or unsupplied standards.

If a user asks for information not in the controlled sources, the correct result is `ReferenceGap`, not external lookup.
