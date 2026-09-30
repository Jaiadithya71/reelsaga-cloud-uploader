# One-time home-PC Google setup

Development bootstrap built, not live-tested with Google. No hosted callback.
The audit still needs public homepage/privacy information; this route removes
only the OAuth callback server, not all website/storage requirements.

## Before running
1. Use existing project157426279644, dramacps-youtube-pipeline, under the 71
   account. Configure a Desktop OAuth client (not Web); download its JSON onto
   your PC. Do not send or commit this JSON. Existing OAuth is External/Testing,
   with no clients/scopes/test users as last checked September30 08:58 IST.
2. Review youtube.upload and youtube.readonly. These allow upload and read-only
   channel/processing checks. Drive is deliberately not authorized by this
   bootstrap. Add the 71 account as a test user while Testing is active.
3. Python3.10+ and the `keyring` package with Windows Credential Locker, macOS
   Keychain or Linux SecretService must work. No plaintext fallback is allowed.

## Run on the PC
Clone the private repo and run:

    python -m pip install keyring
    python desktop_setup.py --client-json /path/to/client_secret_desktop.json

Read the permissions, type YES to continue, sign in to the 71 account and choose
ReelSaga. A temporary random-port listener binds only127.0.0.1 for up to5minutes.
PKCE and one-use state protect the callback; request URLs/codes are not logged.
The tool verifies the exact ReelSaga channel before storing credentials in the
OS keyring. It never prints tokens or exports a plaintext credential file.

## What this does not do
No video upload, no Drive grant, no audit submission, no GitHub Actions credential
transfer. The cloud worker needs a separately reviewed secure provisioning step.
Do not paste credentials in chat or copy them into Actions YAML/repo files.
Testing refresh tokens expire after7days for these scopes; long-term operation
requires the right production configuration. Account access stays off by default.

The bootstrap refuses a non-Desktop client, missing scopes/refresh token, wrong
channel, unsupported keyring or incomplete callback. It makes no automatic retry.
If authorization succeeded but validation failed, Google may still hold a grant;
review/revoke that app in Google Account permissions before starting over.

Sources:
https://developers.google.com/identity/protocols/oauth2/native-app
https://developers.google.com/youtube/v3/docs/channels/list
https://keyring.readthedocs.io/en/latest/

## Proposed separate Actions transfer
After scope/repo transfer approval, install/sign into GitHub CLI on the PC and
run `python provision_actions.py`. It reads OS keyring and pipes credentials to
`gh secret set` on the exact private uploader repo. GitHub CLI encrypts the secret.
No token is printed/exported. This helper is not yet live-tested or approved for
execution. It does not activate the worker or solve backend/Drive/relay gaps.
