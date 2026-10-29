import requests,io,zipfile,pathlib,json,subprocess
root=pathlib.Path('null-dialogue-qa');root.mkdir(exist_ok=True)
u='https://cps-distr.ikyuedu.com/distribution/11/DramaBox资源包-42000029033-19b48bade6b3906f40a7fafe28d1b268.zip';s=requests.Session();r=s.head(u,timeout=30);r.raise_for_status();size=int(r.headers['Content-Length'])
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
z=zipfile.ZipFile(Remote());p=root/'Episode7.mp4';p.write_bytes(z.read('Episode7.mp4'))
subprocess.run(['ffmpeg','-v','error','-ss','30','-i',str(p),'-t','25','-vf','scale=540:960','-c:v','libx264','-preset','fast','-crf','22','-c:a','aac','-y',str(root/'e7-dialogue-30to55.mp4')],check=True)
for sec in range(37,51):subprocess.run(['ffmpeg','-v','error','-ss',str(sec),'-i',str(p),'-frames:v','1','-vf','scale=360:640','-y',str(root/f'e7-{sec}.jpg')],check=True)
p.unlink()
