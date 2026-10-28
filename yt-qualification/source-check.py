import urllib.request,pathlib,json,subprocess,hashlib
u='https://outin-c6b1636ee48611f0bf9400163e01d238.oss-us-west-1.aliyuncs.com/original/workflow/1d936a50-1a162990c9d-0005-9573-534-c9280.mp4'
p=pathlib.Path('qualification/source.mp4');p.parent.mkdir(exist_ok=True)
with urllib.request.urlopen(u,timeout=90)as rr:p.write_bytes(rr.read(300000001))
assert p.stat().st_size<300000000
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
pathlib.Path('qualification/probe.json').write_text(json.dumps(meta,indent=2))
for sec in [2,10,30]:subprocess.run(['ffmpeg','-v','error','-ss',str(sec),'-i',str(p),'-frames:v','1','-y','qualification/frame-'+str(sec)+'.jpg'],check=True)
