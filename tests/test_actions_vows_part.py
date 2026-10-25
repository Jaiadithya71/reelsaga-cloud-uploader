import unittest,json,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
import actions_vows_part as m
class VowsTests(unittest.TestCase):
 def test_all_manifests(self):
  for ep,count in m.COUNTS.items():
   for part in range(1,count+1):
    with patch.object(m,'EP',ep),patch.object(m,'PART',str(part)):
     path=f'vows-prepared/ep{ep}-part{part}.mp4';m.validate(json.loads(Path(path).with_suffix('.json').read_text()),path)
 def test_changes_blocked(self):
  item=json.loads(Path('vows-prepared/ep1-part1.json').read_text());path='vows-prepared/ep1-part1.mp4'
  for changes in ({'sha256':'0'*64},{'title':'wrong'},{'description':'wrong'},{'id':'wrong'}):
   with self.assertRaises(RuntimeError):m.validate(dict(item,**changes),path)
