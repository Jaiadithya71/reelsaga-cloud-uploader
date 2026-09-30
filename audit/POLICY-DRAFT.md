# ReelSaga Upload Queue: proposed privacy practices

DRAFT FOR OWNER REVIEW. Not an effective public privacy policy. The actual
implementation, operator contact, URLs, retention schedule and processors must
match before publication.

Purpose: a private tool for the owner to queue reviewed media and metadata for
upload to their own connected accounts. Proposed data: selected source media,
queue metadata, hashes, destination account/channel IDs, OAuth credentials and
upload session/container/video IDs. No unrelated inbox or Drive files are needed.

Use: validate the requested upload and destination, transfer reviewed media,
resume interrupted uploads safely and stop duplicate or uncertain writes.
Google user data is not sold, used for advertising targeting, or used to train
models. Published videos remain subject to the platform's own policies.

Proposed storage: encrypted credential storage and a private durable ledger.
Remote storage/relay vendors and actual deletion periods remain undecided;
no claim of an implemented encryption or retention guarantee is made here.
Actions must not log credentials, media URLs or secrets or retain video artifacts.

Control: owner can pause pending work, revoke Google access, and request deletion
of local/remote app-held data. Disconnect must stop future calls and invalidate
credentials. Deleting queue data is distinct from deleting a published platform
video; platform deletion requires a separate explicit choice. An unresolved
upload must be reconciled before its identifiers are erased to avoid duplicates.

Public version must include operator contact, Google Privacy Policy link,
YouTube Terms of Service acknowledgement, revocation instructions, actual
retention/deletion timelines and disclosures matching the selected processors.
Google API data use must comply with the Google API Services User Data Policy,
including Limited Use requirements.
