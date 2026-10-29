import requests,io,zipfile,pathlib,subprocess,json,hashlib,os
e=int(os.environ.get('NULL_EP','1'));part=int(os.environ.get('NULL_PART','1'));bounds=json.loads(pathlib.Path('null-candidate-bounds.json').read_text())['bounds'][str(e)];assert 1<=part<len(bounds);start,end=bounds[part-1:part+1];length=end-start;assert 0<length<=55
def require(ok,why):
 if not ok:raise RuntimeError(why)
import requests,io,zipfile
u='https://cps-distr.ikyuedu.com/distribution/11/DramaBox资源包-42000029033-19b48bade6b3906f40a7fafe28d1b268.zip'
sess=requests.Session();rr=sess.head(u,timeout=30);rr.raise_for_status();size=int(rr.headers['Content-Length'])
class Remote(io.RawIOBase):
 def __init__(self):self.pos=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,o,w=0):self.pos=o if w==0 else self.pos+o if w==1 else size+o;return self.pos
 def read(self,n=-1):
  if n<0:n=size-self.pos
  n=min(n,size-self.pos)
  if n<=0:return b''
  rr=sess.get(u,headers={'Range':f'bytes={self.pos}-{min(size-1,self.pos+n-1)}'},timeout=45);rr.raise_for_status();require(rr.status_code==206,'Source range unsupported');self.pos+=len(rr.content);return rr.content
z=zipfile.ZipFile(Remote());pathlib.Path('source.mp4').write_bytes(z.read(f'Episode{e}.mp4'))
subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-ss',str(start),'-i','source.mp4','-t',str(length),'-vf',f'fade=t=in:st=0:d=0.5,fade=t=out:st={length-.5}:d=0.5','-af',f'afade=t=in:st=0:d=0.5,afade=t=out:st={length-.5}:d=0.5','-c:v','libx264','-threads:v','3','-preset','ultrafast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-y','p1.mp4'],check=True)
p=pathlib.Path('p1.mp4');subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True);pathlib.Path('render-receipt.json').write_text(json.dumps({'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2))
