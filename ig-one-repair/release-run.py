import runpy,traceback,pathlib,json
try:runpy.run_path('ig-one-repair/release.py',run_name='__main__')
except BaseException as e:
 frames=traceback.extract_tb(e.__traceback__);pathlib.Path('release-stop.json').write_text(json.dumps({'type':type(e).__name__,'frames':[{'file':pathlib.Path(f.filename).name,'line':f.lineno}for f in frames]}));print('ONE_RELEASE_STOP',type(e).__name__,'reconcile existing draft ID, never create or release blindly');raise SystemExit(1)from None
