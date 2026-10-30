"""Source/render QA only for the candidate free episodes, not release authorization. No account writes."""
import requests,io,zipfile,pathlib,json,subprocess,hashlib
root=pathlib.Path('saved-source-qa');root.mkdir(exist_ok=True)
u='https://cps-distr.ikyuedu.com/distribution/9/DramaBox资源包-42000029091-8a860067138527188991e3f8847005db.zip';s=requests.Session();r=s.head(u,timeout=30);r.raise_for_status();size=int(r.headers['Content-Length'])
class Remote(io.RawIOBase):
 def __init__(self):self.pos=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,o,w=0):self.pos=o if w==0 else self.pos+o if w==1 else size+o;return self.pos
 def read(self,n=-1):
  n=min(n if n>=0 else size-self.pos,size-self.pos)
  if n<=0:return b''
  r=s.get(u,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'},timeout=90);r.raise_for_status();assert r.status_code==206 and len(r.content)==n;self.pos+=n;return r.content
z=zipfile.ZipFile(Remote());bounds=json.loads(pathlib.Path('saved-candidate-bounds.json').read_text())['bounds'];proof=[]
for ep in range(1,10):
 src=pathlib.Path('source.mp4');src.write_bytes(z.read(f'Episode{ep}.mp4'));bs=bounds[str(ep)]
 for n,(start,end)in enumerate(zip(bs,bs[1:]),1):
  length=end-start;assert 0<length<=55;p=root/f'e{ep}p{n}.mp4'
  subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-ss',str(start),'-i',str(src),'-t',str(length),'-vf',f'fade=t=in:st=0:d=0.5,fade=t=out:st={length-.5}:d=0.5','-af',f'afade=t=in:st=0:d=0.5,afade=t=out:st={length-.5}:d=0.5','-c:v','libx264','-threads:v','2','-preset','ultrafast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-y',str(p)],check=True)
  subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True)
  for label,t in [('head',0),('tail',length-4)]:subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-t','4','-vn','-y',str(root/f'e{ep}p{n}-{label}.wav')],check=True)
  proof.append({'episode':ep,'part':n,'start':start,'end':end,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 src.unlink()
(root/'render-receipts.json').write_text(json.dumps(proof,indent=2))
