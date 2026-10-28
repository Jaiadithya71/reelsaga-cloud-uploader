import os,hashlib,base64,pathlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
s=os.environ.pop('REELSAGA_CLOUDINARY_API_SECRET').encode()
key=hashlib.sha256(b'reelsaga-synthetic-manifest-v1\0'+s).digest()
b=base64.b64decode(pathlib.Path('synthetic-probe/manifest.enc.b64').read_text())
p=pathlib.Path('manifest.json');p.write_bytes(AESGCM(key).decrypt(b[:12],b[12:],None));os.chmod(p,0o600)
