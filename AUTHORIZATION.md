# Account authorization checklist

No tokens should be pasted into chat, committed, or printed in workflow logs.
No Google/Meta setup has been submitted in this preparation run. Existing Google project157426279644 (dramacps-youtube-pipeline) was verified live September30: YouTube API enabled, OAuth External/Testing, no clients/scopes/test users. Owner deferred the authorization steps.

## Google, account [owner-gmail-redacted]

1. Create or select a Google Cloud project and enable Drive API and YouTube Data API v3. No billing account needed for these upload calls.
2. Configure an OAuth consent screen and an OAuth client for the selected auth callback. Request offline access for a refresh token. Verify the actual ReelSaga channel ID before any upload.
3. YouTube upload permission is `https://www.googleapis.com/auth/youtube.upload`. Identity and processing-read checks need an additional read scope, to be shown separately before approval.
4. Drive scope needs a decision before consent. `drive.file` is narrow, but grants only app-created or individually app-selected files. Selecting a folder does not by itself grant every newly dragged child file. A producer using the same app to upload each MP4 avoids broad Drive access. A normal folder that receives arbitrary dragged videos instead needs broader read access or per-file selection. Do not silently request full Drive access.
5. Authenticate the 71 account and verify channel `UC71kSXnAt6Ipy7KqVVo3mdA`, not just the email. Keep credentials in secure storage and GitHub Actions encrypted secrets.
6. External OAuth apps in Testing get seven-day refresh tokens for these scopes. Testing is not unattended long-term auth. Resolve production/verification status before claiming durable operation.
7. YouTube API project audit is separate from OAuth consent verification. Until audit, uploads are forced Private and cannot be treated as a public publishing queue. Browser publishing continues separately. No duplicate private uploads of already Public videos.

## Meta, reelsaga3000

Creator conversion is verified in live settings. Instagram Login does not need a Facebook Page.

1. Sign into the owner's Meta developer account. Create/select a Business-type app with Instagram product and "API setup with Instagram login". Do not choose Facebook Login merely to bypass setup.
2. Add the owner's public Instagram account under the app's roles/account setup. Standard Access is for the accounts owned/managed by the app operator; wider accounts need Advanced Access/App Review.
3. Grant `instagram_business_basic` and `instagram_business_content_publish`. Read back `/me` user ID, username and account type before binding the destination.
4. For the owner's initial canary, the dashboard's Generate token route provides a long-lived 60-day token. The Business Login OAuth route provides a one-hour token exchanged server-side for 60 days. Save tokens securely, not via chat. Add expiry/refresh monitoring.
5. Instagram Login media publishing requires a publicly fetchable HTTPS MP4 URL. Ordinary private Drive links are not a verified media relay. No Drive sharing permission is changed here. A scoped short-lived relay still needs selection/approval; until then API Instagram execution is disabled.
6. Confirm a single canary's saved caption, pixels and playback before scheduled publishing. Preserve container/media IDs and pause uncertain writes, never recreate blindly.

## GitHub Actions

Verified account is GitHub Free. Actions account budget is $0 with Stop usage Yes.
Use only standard Linux runners, a short timeout, serialized jobs and no video artifacts.
The six-hour workflow is gated off by default. Even when enabled it runs tests and
read-only preflight only. It does not call these adapters yet.
Secrets to provision when ready: Google client config + refresh token, Instagram
access token and app config. Durable remote state and media relay are not wired.

## Sources checked September 30, 2026

- https://developers.google.com/drive/api/guides/api-specific-auth
- https://developers.google.com/identity/protocols/oauth2
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/youtube/v3/docs/videos/insert
- https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
- https://developers.facebook.com/docs/instagram-platform/overview
- https://developers.facebook.com/docs/instagram-platform/create-an-instagram-app
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing/
- https://developers.facebook.com/docs/instagram-platform/reference/access_token/
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
