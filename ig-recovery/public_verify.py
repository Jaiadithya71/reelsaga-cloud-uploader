"""Verify delivered frames against exact original. No login or platform writes."""
import re,json,html,pathlib,subprocess,tempfile,urllib.parse,urllib.request
import numpy as np
from PIL import Image
class VerificationError(RuntimeError):pass
def require(ok,why):
 if not ok:raise VerificationError(why)
def fetch(url,limit):
 p=urllib.parse.urlsplit(url);require(p.scheme=='https'and(p.hostname=='www.instagram.com'or p.hostname.endswith('.cdninstagram.com')or p.hostname.endswith('.fbcdn.net')),'Unexpected media origin')
 with urllib.request.urlopen(url,timeout=90)as r:
  final=urllib.parse.urlsplit(r.url);require(final.scheme=='https'and(final.hostname=='www.instagram.com'or final.hostname.endswith('.cdninstagram.com')or final.hostname.endswith('.fbcdn.net')),'Unexpected redirect');d=r.read(limit+1)
 require(len(d)<=limit,'Response too large');return d
def frame(file,t,out):subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(file),'-frames:v','1','-vf','scale=360:640','-y',str(out)],check=True,capture_output=True)
def similarity(a,b):
 a=np.asarray(Image.open(a).convert('RGB').resize((360,640)),dtype=float);b=np.asarray(Image.open(b).convert('RGB').resize((360,640)),dtype=float)
 return {'correlation':float(np.corrcoef(a.ravel(),b.ravel())[0,1]),'mean_error':float(np.abs(a-b).mean())}
def verify(link,original,caption,cover_ms,outdir):
 p=urllib.parse.urlsplit(link);require(p.hostname=='www.instagram.com','Unexpected reel domain');m=re.fullmatch(r'/(?:reel|reels)/([A-Za-z0-9_-]+)/?',p.path);require(m,'Unexpected reel URL');code=m.group(1);d=pathlib.Path(outdir);d.mkdir(parents=True,exist_ok=True)
 s=fetch('https://www.instagram.com/reel/'+code+'/embed/',5_000_000).decode();require('EmbeddedMediaImage'in s and code in s,'No actual embedded media')
 m=re.search(r'\\"video_url\\":\\"(.*?)\\"',s);require(m,'No served video URL');video_url=json.loads('"'+m.group(1)+'"').replace('\\/','/')
 m=re.search(r'<img class="EmbeddedMediaImage"[^>]*src="([^"]+)"',s);require(m,'No served cover');cover_url=html.unescape(m.group(1));v=d/'served.mp4';c=d/'cover.jpg';v.write_bytes(fetch(video_url,200_000_000));c.write_bytes(fetch(cover_url,5_000_000))
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(v)]));orig=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(original)]));vv=next(x for x in meta['streams']if x['codec_type']=='video');ov=next(x for x in orig['streams']if x['codec_type']=='video');duration=float(meta['format']['duration']);require(abs(duration-float(orig['format']['duration']))<.3,'Duration changed');require(abs(vv['width']/vv['height']-ov['width']/ov['height'])<.003,'Frame cropped');require(any(x['codec_type']=='audio'for x in meta['streams']),'No served audio')
 subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],check=True,capture_output=True)
 results=[]
 for j,t in enumerate([cover_ms/1000,min(10,duration*.25),duration*.5,max(2,duration-5)]):
  a=d/f'original-{j}.png';b=d/f'served-{j}.png';frame(original,t,a);frame(v,t,b);score=similarity(a,b);require(score['correlation']>.97 and score['mean_error']<12,'Served frame differs from original');results.append(dict(seconds=t,**score))
 a=d/'original-cover.png';frame(original,cover_ms/1000,a);score=similarity(a,c);require(score['correlation']>.95 and score['mean_error']<15,'Public cover differs');require(np.asarray(Image.open(c)).mean()>12,'Black public cover')
 # Exact caption in embed is JavaScript string-escaped. Normalize only the serialization layer.
 cm=re.search(r'edge_media_to_caption.*?\\"text\\":\\"(.*?)\\"\}\}',s);require(cm,'Public caption absent');public_caption=json.loads('"'+json.loads('"'+cm.group(1)+'"')+'"');require(public_caption.strip()==caption.strip(),'Public caption differs')
 receipt={'shortcode':code,'width':vv['width'],'height':vv['height'],'duration':duration,'audio_present':True,'decode_ok':True,'frames':results,'cover':score,'status':'public_frame_and_cover_match'};(d/'verification-receipt.json').write_text(json.dumps(receipt,indent=2));return receipt
if __name__=='__main__':
 import sys
 print(json.dumps(verify(sys.argv[1],sys.argv[2],pathlib.Path(sys.argv[3]).read_text(),int(sys.argv[4]),sys.argv[5]),indent=2))
