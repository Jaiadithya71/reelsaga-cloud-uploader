import os,json,pathlib,datetime
from buffer_client import Buffer
b=Buffer(os.environ.pop('REELSAGA_BUFFER_API_KEY'));ch=b.channel('6adb4d02778b240e2f9c6d48');rows=b.inventory('6adb4a329ef1e740831f7879','6adb4d02778b240e2f9c6d48');counts={}
for p in rows:counts[p['status']]=counts.get(p['status'],0)+1
now=datetime.datetime.now(datetime.timezone.utc);recent=[p for p in rows if p.get('sentAt')and(now-datetime.datetime.fromisoformat(p['sentAt'].replace('Z','+00:00'))).total_seconds()<86400]
pathlib.Path('inventory-receipt.json').write_text(json.dumps({'channel':ch,'complete':rows.complete,'count':len(rows),'status_counts':counts,'last24h_sent':len(recent),'latest':[{'id':p['id'],'status':p['status'],'sent_at':p.get('sentAt'),'due_at':p.get('dueAt'),'firstline':p.get('text','').splitlines()[0]if p.get('text')else ''}for p in sorted(rows,key=lambda p:p.get('sentAt')or p.get('dueAt')or'',reverse=True)[:5]]},indent=2))
