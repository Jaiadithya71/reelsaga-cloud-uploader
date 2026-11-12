"""Delete one consumed stage. Keep evidence/secrets until every readback passes."""
import json,pathlib,sys

def cleanup(loc_path,url_path,client,get,secret_paths=()):
    loc_path=pathlib.Path(loc_path);url_path=pathlib.Path(url_path)
    loc=json.loads(loc_path.read_text());url=url_path.read_text().strip()
    if loc['bucket']!='reelsaga-private-staging-71' or not loc['key'].startswith('xfer/'):
        raise RuntimeError('Unexpected stage destination')
    client.delete_object(Bucket=loc['bucket'],Key=loc['key'])
    try:client.head_object(Bucket=loc['bucket'],Key=loc['key'])
    except Exception as exc:
        if getattr(exc,'response',{}).get('ResponseMetadata',{}).get('HTTPStatusCode')!=404:raise
    else:raise RuntimeError('Stage still exists')
    response=get(url,timeout=30)
    if response.status_code!=404:raise RuntimeError('Original signed read is not 404; evidence retained')
    loc.update(deleted=True,head_404=True,original_signed_get_404=True)
    tmp=loc_path.with_suffix('.tmp');tmp.write_text(json.dumps(loc));tmp.replace(loc_path)
    url_path.unlink()
    for path in secret_paths:pathlib.Path(path).unlink(missing_ok=True)
    return loc

if __name__=='__main__':
    import boto3,requests
    from botocore.config import Config
    p=pathlib.Path('/home/sandbox/.vault/tigris-reelsaga-staging-s3-worker-42f1cb')
    client=boto3.client('s3',endpoint_url='https://t3.storage.dev',region_name='auto',aws_access_key_id=(p/'username').read_text().strip(),aws_secret_access_key=(p/'password').read_text().strip(),config=Config(signature_version='s3v4',retries={'total_max_attempts':1},s3={'addressing_style':'path'}))
    cleanup(sys.argv[1],sys.argv[2],client,requests.get,[p/'username',p/'password'])
    print('Exact stage cleanup verified HEAD404 originalsignedGET404; link and temporary credentials removed')
