# Exact next Console setup draft

No changes submitted. Last live check September30 08:58 IST:
Project157426279644/dramacps-youtube-pipeline,71account; YouTube API enabled.
OAuth External/Testing; no clients,scopes,test users. Recheck before mutation.

1. Google Auth Platform Branding: proposed app name ReelSaga Upload Queue,
   support/developer contact71email. Do not invent public homepage/privacy URL;
   approved published information pages still need creating.
2. Audience: External,keep Testing for canary. Add71email as a test user after
   exact scopes review. Do not click Publish app until actual setup is ready.
3. Data Access: youtube.upload + youtube.readonly for this initial bootstrap.
   No drive.readonly,drive.file or unrelated scopes in this initial grant.
4. Clients: Create OAuth client,application type Desktop app. Download JSON
   directly onto owner's PC; not chat,repo,public website or Actions artifact.
5. Run desktop_setup.py on owner's PC. Native OS keyring required. Verify exact
   ReelSaga channel. This does not connect Drive or activate cloud scheduling.
6. Separate reviewed transfer via provision_actions.py and authenticated GitHub
   CLI to the exact private repository secret. Do not activate worker before
   real ledger/control/canary tests and owner publishing scope pass.

Reviewed draft name/contact may be used for configuration; no final audit
submission is authorized by these setup steps. Testing refresh token7-day limit
still prevents claiming long-term unattended reliability.
