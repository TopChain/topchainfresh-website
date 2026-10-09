"""Private Gmail relay helper. Never publish its environment or queue output."""
import json,os,pathlib,sys,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def request(action,payload=None,admin=True):
    config={}
    private=ROOT/'.env.subscriptions'
    if private.exists():config=dict(line.split('=',1) for line in private.read_text().splitlines() if '=' in line)
    config.update({key:os.environ[key] for key in ('MAILER_SECRET','SUBSCRIPTION_ENDPOINT') if os.environ.get(key)})
    headers={'Content-Type':'application/json'}
    if admin:headers['Authorization']='Bearer '+config['MAILER_SECRET']
    else:headers['Origin']='https://www.topchainfresh.com'
    req=urllib.request.Request(config['SUBSCRIPTION_ENDPOINT']+'?action='+action,data=json.dumps(payload or {}).encode(),headers=headers,method='POST')
    with urllib.request.urlopen(req,timeout=25) as response:return json.load(response)
if __name__=='__main__':
    action=sys.argv[1]
    payload=json.loads(sys.stdin.read()) if action=='mail-result' else {}
    print(json.dumps(request(action,payload),ensure_ascii=False))
