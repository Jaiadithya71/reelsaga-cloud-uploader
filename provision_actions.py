"""Owner-run secret provisioning. No token output or workflow activation.

GitHub CLI handles encryption. Owner must separately approve the exact repo and
credential scope. This is a proposed route, not an automatically run step.
"""
import json
import subprocess
from desktop_setup import secure_keyring,SERVICE,ACCOUNT,CHANNEL,SCOPES

REPO='Jaiadithya71/reelsaga-cloud-uploader'
SECRET='REELSAGA_GOOGLE_CREDENTIALS'
class ProvisionError(RuntimeError):pass

def validated_record(raw):
    data=json.loads(raw)
    if data.get('channel_id')!=CHANNEL or not set(SCOPES)<=set(data.get('granted_scopes',[])):
        raise ProvisionError('Destination/grant mismatch')
    if not all(data.get(k) for k in ('client_id','client_secret','refresh_token')):
        raise ProvisionError('Credential record incomplete')
    return data

def provision(raw,run=subprocess.run):
    data=validated_record(raw)
    # subprocess argv and logs contain no credentials. Capture/suppress output.
    result=run(['gh','secret','set',SECRET,'--repo',REPO],
               input=json.dumps(data),text=True,capture_output=True,timeout=45)
    if result.returncode!=0:raise ProvisionError('Secret update not confirmed; no retry')

def main():
    print('Proposed destination: '+REPO+' / '+SECRET)
    print('Copies your stored YouTube upload/read grant into this private repo secret.')
    print('Does not enable Actions publishing. No Drive grant is included.')
    if input('Approve this exact transfer? Type COPY: ').strip()!='COPY':
        raise ProvisionError('Transfer cancelled')
    raw=secure_keyring().get_password(SERVICE,ACCOUNT)
    if not raw:raise ProvisionError('Run Desktop setup first')
    try:provision(raw)
    except Exception:raise ProvisionError('Secret transfer not confirmed; no credentials shown') from None
    print('Secret set. Workflow remains off; backend/canary controls still required.')

if __name__=='__main__':
    try:main()
    except Exception:
        print('Provisioning stopped. No secrets shown. Verify GitHub login/repo access.')
        raise SystemExit(1)
