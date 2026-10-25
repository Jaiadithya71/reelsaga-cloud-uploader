# Drive queue layout (not created yet)

Use account [owner-gmail-redacted]. Proposed private folder name: ReelSaga Queue.
No files, folder, shares, OAuth grants, or billing services have been created.

Proposed child layout:

- media/: source-resolution verified part MP4s
- manifests/: versioned JSON with item IDs, SHA256 and exact reviewed metadata
- state/: remote state checkpoints, not public and not workflow artifacts
- quarantine/: items needing human reconciliation or failed quality checks

Do not use filenames alone as identity. An item ID stays fixed after claim.
Do not add already-public videos to an API upload queue. Import their actual saved
IDs as completed inventory instead. The current public YouTube inventory includes
Blood Pact 30 parts and Daddy EP1 P1/P2. Instagram Blood Pact EP1 P1 is published.

The narrow Drive scope design requires media uploaded through the same authorized
app or individually selected. For arbitrary drag-and-drop folder ingestion, a
separately reviewed broader read scope is needed. Folder layout is not an OAuth
grant. No fake Drive IDs or synthetic publishing-ready entries are included.

Before activation: choose a durable transactional remote state backend and a
short-lived public HTTPS media relay. A signed relay URL is a scoped disclosure of
that video to anyone holding it; preserve owner-approved audience, expire it and
avoid public directory listing. Do not expose the entire Drive folder.
