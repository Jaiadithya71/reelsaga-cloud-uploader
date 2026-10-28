import runpy
try:runpy.run_path('ig-one-repair/release.py',run_name='__main__')
except BaseException as e:
 print('ONE_RELEASE_STOP',type(e).__name__,'reconcile existing draft ID, never create or release blindly')
 raise SystemExit(1)from None
