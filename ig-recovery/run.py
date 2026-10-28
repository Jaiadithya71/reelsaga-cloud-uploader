import runpy,pathlib,json,traceback
try:runpy.run_path('ig-recovery/runner.py',run_name='__main__')
except BaseException as e:
 if isinstance(e,SystemExit)and e.code in(None,0):raise
 frames=traceback.extract_tb(e.__traceback__);pathlib.Path('recovery-stop.json').write_text(json.dumps({'type':type(e).__name__,'frames':[{'file':pathlib.Path(f.filename).name,'line':f.lineno}for f in frames]}));print('RECOVERY_HELD',type(e).__name__,'reconcile durable exact IDs; never retry blindly');raise SystemExit(1)from None
