import requests,io,zipfile,pathlib,subprocess,json,hashlib
def require(ok,why):
 if not ok:raise RuntimeError(why)
import requests,io,zipfile
u='https://cps-distr.ikyuedu.com/distribution/9/DramaBox资源包-42000028903-19e7e89829848a1e130e65a6c710e035.zip'
sess=requests.Session();rr=sess.head(u,timeout=30);rr.raise_for_status();size=int(rr.headers['Content-Length'])
class Remote(io.RawIOBase):
 def __init__(self):self.pos=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,o,w=0):self.pos=o if w==0 else self.pos+o if w==1 else size+o;return self.pos
 def read(self,n=-1):
  if n<0:n=size-self.pos
  if not n:return b''
  rr=sess.get(u,headers={'Range':f'bytes={self.pos}-{min(size-1,self.pos+n-1)}'},timeout=45);rr.raise_for_status();require(rr.status_code==206,'Source range unsupported');self.pos+=len(rr.content);return rr.content
z=zipfile.ZipFile(Remote());pathlib.Path('source.mp4').write_bytes(z.read('Episode1.mp4'))
subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-ss','0','-i','source.mp4','-t','35.4','-vf','fade=t=in:st=0:d=0.5,fade=t=out:st=34.9:d=0.5','-af','afade=t=in:st=0:d=0.5,afade=t=out:st=34.9:d=0.5','-c:v','libx264','-threads:v','3','-preset','ultrafast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-y','p1.mp4'],check=True)
p=pathlib.Path('p1.mp4');subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True);pathlib.Path('render-receipt.json').write_text(json.dumps({'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2))
