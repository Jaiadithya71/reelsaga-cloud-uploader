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
z=zipfile.ZipFile(Remote())
bounds={1:[0,35.4,80,132.8,171.29],2:[0,47.36,85.36,127.04,171.247],3:[0,35.6,70.88,107.396],4:[0,38.4,77.44,118.88,157.551],5:[0,51,93.16,138.522],6:[0,33.4,68.08,101.551],7:[0,40.4,88,120.73],8:[0,34.12,67.92,101.53],9:[0,40.2,82.24,123.396]}
out=pathlib.Path('golden-renderqa');out.mkdir(exist_ok=True);receipts=[]
for e,bs in bounds.items():
 pathlib.Path('source.mp4').write_bytes(z.read(f'Episode{e}.mp4'))
 for part,(start,end)in enumerate(zip(bs,bs[1:]),1):
  length=end-start;target=pathlib.Path('p1.mp4')
  subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-ss',str(start),'-i','source.mp4','-t',str(length),'-vf',f'fade=t=in:st=0:d=0.5,fade=t=out:st={length-.5}:d=0.5','-af',f'afade=t=in:st=0:d=0.5,afade=t=out:st={length-.5}:d=0.5','-c:v','libx264','-threads:v','3','-preset','ultrafast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-y',str(target)],check=True)
  subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'],check=True)
  md5=subprocess.check_output(['ffmpeg','-v','error','-i',str(target),'-map','0:v','-f','framemd5','-']);lines=[l for l in md5.decode().splitlines()if not l.startswith('#')]
  meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]))
  receipts.append({'episode':e,'part':part,'start':start,'end':end,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'decoded_frame_hash':hashlib.sha256('\n'.join(lines).encode()).hexdigest(),'frame_count':len(lines),'metadata':meta})
  subprocess.run(['ffmpeg','-v','error','-ss','0.6','-i',str(target),'-frames:v','1','-vf','scale=216:384','-y',str(out/f'e{e}p{part}-cover.jpg')],check=True)
  (out/'receipts.json').write_text(json.dumps(receipts,indent=2));print('rendered',e,part,flush=True)
