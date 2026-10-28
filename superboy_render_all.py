import os,json,pathlib,urllib.request,urllib.parse,hashlib,subprocess,math
sources=json.loads(os.environ['SOURCES_JSON']);assert len(sources)==11;result=[]
for e,source in enumerate(sources,1):
 d=pathlib.Path('superboy')/f'e{e}';d.mkdir(parents=True);u=source['href'];assert urllib.parse.urlsplit(u).hostname=='v-out.oss-accelerate.aliyuncs.com'
 data=urllib.request.urlopen(u,timeout=120).read(400000000);p=d/'source.mp4';p.write_bytes(data)
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]));v=next(x for x in meta['streams']if x['codec_type']=='video');assert v['width']>=720 and v['height']>=1280 and any(x['codec_type']=='audio'for x in meta['streams']);duration=float(meta['format']['duration']);subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True)
 rec={'episode':e,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'duration':duration,'metadata':meta};n=math.ceil(duration/55);length=duration/n;parts=[]
 for k in range(n):
  out=d/f'part{k+1}.mp4';fade=f'fade=t=in:st=0:d=0.5,fade=t=out:st={length-.5}:d=0.5'
  subprocess.run(['ffmpeg','-v','error','-cpuflags','0','-filter_threads','1','-ss',str(k*length),'-i',str(p),'-t',str(length),'-vf',fade,'-af',fade.replace('fade','afade'),'-c:v','libx264','-threads:v','3','-x264-params','asm=0','-preset','ultrafast','-crf','18','-c:a','aac','-flags:a','+bitexact','-b:a','192k','-movflags','+faststart','-y',str(out)],check=True)
  pm=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]));assert float(pm['format']['duration'])<55.1;subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True)
  frame=d/f'part{k+1}-frame.jpg';subprocess.run(['ffmpeg','-v','error','-ss','2','-i',str(out),'-frames:v','1','-vf','scale=360:640','-y',str(frame)],check=True)
  parts.append({'part':k+1,'parts':n,'source_start':k*length,'source_end':(k+1)*length,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'duration':float(pm['format']['duration']),'file':str(out)})
 result.append({'episode':e,'source':rec,'parts':parts});pathlib.Path('superboy-render-receipt.json').write_text(json.dumps(result,indent=2));p.unlink()
