"""Normalize only byte-identical approved renderer output; never transcode."""
import hashlib,pathlib,shutil
def normalize_original(root,size,sha):
 root=pathlib.Path(root)
 target=root/'p1.mp4'
 def matches(p):return p.is_file() and p.stat().st_size==size and hashlib.sha256(p.read_bytes()).hexdigest()==sha
 if matches(target):return target
 candidates=[p for p in root.rglob('*.mp4') if '.git'not in p.parts and matches(p)]
 if len(candidates)!=1:raise RuntimeError('Expected one exact approved original renderer output')
 shutil.copyfile(candidates[0],target)
 if not matches(target):raise RuntimeError('Normalized original differs')
 return target
