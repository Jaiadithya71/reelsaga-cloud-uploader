"""Offline, deterministic subtitle-only correction. No account access or publication."""
import argparse,hashlib,json,pathlib,subprocess,tempfile

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audio_sha(path):return hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c','copy','-f','adts','-'])).hexdigest()
def apply(source,destination,fix,font):
 if sha(source)!=fix['source_sha256']:raise ValueError('Source hash differs; stop')
 if destination.exists():raise ValueError('Destination exists; never overwrite verified master')
 patches=fix.get('patches',[fix])
 with tempfile.TemporaryDirectory()as td:
  filters=[]
  for i,patch in enumerate(patches):
   a,b=patch['timing'];x,y,w,h=patch['rect']
   if not(0<=a<b and 0<=x<x+w<=1080 and 0<=y<y+h<=1920):raise ValueError('Invalid correction bounds')
   text=pathlib.Path(td)/f'line-{i}.txt';text.write_text(patch['text'])
   filters.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=black:t=fill:enable='between(t,{a},{b})',drawtext=fontfile={font}:textfile={text}:fontcolor=white:fontsize=46:borderw=2:bordercolor=black:line_spacing=9:x=(w-text_w)/2:y={y+12}:enable='between(t,{a},{b})'")
  vf=','.join(filters)
  subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(source),'-vf',vf,'-c:v','libx264','-threads:v','2','-preset','ultrafast','-crf','18','-c:a','copy','-movflags','+faststart','-y',str(destination)],check=True)
 if audio_sha(source)!=audio_sha(destination):raise ValueError('Audio stream changed; reject candidate')
 if sha(destination)!=fix['new_sha256']:raise ValueError('Candidate differs from expected render; requires new verification, not publication')
 return {'sha256':sha(destination),'audio_byte_exact':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--recipe',type=pathlib.Path,required=True);p.add_argument('--part',required=True);p.add_argument('--font',default='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');a=p.parse_args();r=json.loads(a.recipe.read_text());f=next(x for x in r['fixes']if x['part']==a.part);print(json.dumps(apply(a.source,a.output,f,a.font)))
