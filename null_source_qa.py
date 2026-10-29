import requests,io,zipfile,pathlib,json,subprocess
root=pathlib.Path('null-source-qa');root.mkdir(exist_ok=True);u='https://cps-distr.ikyuedu.com/distribution/11/DramaBox资源包-42000029033-19b48bade6b3906f40a7fafe28d1b268.zip';s=requests.Session();r=s.head(u,timeout=25);r.raise_for_status();size=int(r.headers['Content-Length'])
class Remote(io.RawIOBase):
 def __init__(self):self.pos=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,o,w=0):self.pos=o if w==0 else self.pos+o if w==1 else size+o;return self.pos
 def read(self,n=-1):
  if n<0:n=size-self.pos
  if not n:return b''
  r=s.get(u,headers={'Range':f'bytes={self.pos}-{min(size-1,self.pos+n-1)}'},timeout=60);r.raise_for_status();assert r.status_code==206;self.pos+=len(r.content);return r.content
import hashlib
z=zipfile.ZipFile(Remote());members=[x.filename for x in z.infolist() if x.filename.endswith('.mp4')]
results=[]
for name in members:
 p=root/name
 if not p.exists():p.write_bytes(z.read(name))
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
 (root/(name+'.metadata.json')).write_text(json.dumps(meta,indent=2))
 v=next(i for i in meta['streams']if i['codec_type']=='video')
 dec=subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(p),'-f','null','-'],capture_output=True)
 for sec in (2,25):
  subprocess.run(['ffmpeg','-v','error','-ss',str(sec),'-i',str(p),'-frames:v','1','-vf','scale=360:640','-y',str(root/(name+f'.{sec}s.jpg'))],check=True)
 r={'episode':int(name[7:-4]),'duration':float(meta['format']['duration']),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'width':v['width'],'height':v['height'],'audio':any(i['codec_type']=='audio'for i in meta['streams']),'decode':'pass' if dec.returncode==0 and not dec.stderr else 'review','decode_stderr':dec.stderr.decode()[:3000]}
 results.append(r);print(r,flush=True);(root/'all-source-qa.json').write_text(json.dumps(results,indent=2));p.unlink()
