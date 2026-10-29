"""A single conditional write, then exact readback if its acknowledgement is lost."""
import hashlib
from botocore.exceptions import ClientError,EndpointConnectionError,ConnectionClosedError,ReadTimeoutError
from queue_guard import require

def put_once_verified(s3,bucket,key,path,expected_bytes,expected_sha256):
 ambiguous=False
 try:
  with path.open('rb')as body:
   s3.put_object(Bucket=bucket,Key=key,Body=body,ContentType='video/mp4',ACL='public-read',IfNoneMatch='*')
 except ClientError as e:
  if e.response.get('Error',{}).get('Code')not in('PreconditionFailed','ConditionalRequestConflict','RequestTimeout','InternalError','ServiceUnavailable'):raise
  ambiguous=True
 except(EndpointConnectionError,ConnectionClosedError,ReadTimeoutError):
  ambiguous=True
 # No retry, overwrite, key rotation, ACL change or second upload. Even an
 # acknowledged write must have the exact bytes and public-read ACL.
 head=s3.head_object(Bucket=bucket,Key=key)
 require(head['ContentLength']==expected_bytes,'Uploaded size differs')
 obj=s3.get_object(Bucket=bucket,Key=key)
 body=obj['Body']
 try:data=body.read(expected_bytes+1)
 finally:body.close()
 require(len(data)==expected_bytes and hashlib.sha256(data).hexdigest()==expected_sha256,'Uploaded full hash differs')
 acl=s3.get_object_acl(Bucket=bucket,Key=key)
 require(any(g['Grantee'].get('URI','').endswith('/AllUsers')and g['Permission']=='READ'for g in acl['Grants']),'Uploaded public ACL absent')
 return {'single_conditional_put':True,'ambiguous_ack_reconciled':ambiguous,'bytes':expected_bytes,'sha256':expected_sha256}
