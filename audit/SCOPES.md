# Proposed least-privilege scope justification

Not an approved grant. Show final scopes before owner authorization.

- youtube.upload: upload owner-reviewed media/metadata to the owner's channel.
- youtube.readonly (candidate): verify channel identity and read completed upload
  processing records. Confirm method/scope requirements before enabling.
- drive.file (preferred candidate): app-created or individually selected MP4 and
  manifest files only. Selecting a parent folder does not grant arbitrary future
  drag-and-drop children. Broad drive.readonly is not selected or authorized.

OAuth personal-use exception may apply, but it never removes the YouTube audit
requirement. External Testing tokens expire after seven days for these scopes;
resolve production configuration before claiming unattended long-term use.

Sources checked September 30, 2026:
https://support.google.com/cloud/answer/13464323?hl=en
https://support.google.com/cloud/answer/13464321
https://support.google.com/cloud/answer/13804565?hl=en
https://developers.google.com/youtube/v3/docs/videos/insert
https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
https://developers.google.com/drive/api/guides/api-specific-auth
