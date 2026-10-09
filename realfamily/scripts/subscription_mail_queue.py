"""Private Gmail relay helper. Never publish its environment or queue output."""
import json,pathlib,sys,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def request(action,payload=None,admin=True):
    config=dict(line.split('=',1) for line in (ROOT/'.env.subscriptions').read_text().splitlines() if '=' in line)
    headers={'Content-Type':'application/json'}
    if admin:headers['Authorization']='Bearer '+config['MAILER_SECRET']
    else:headers['Origin']='https://www.topchainfresh.com'
    req=urllib.request.Request(config['SUBSCRIPTION_ENDPOINT']+'?action='+action,data=json.dumps(payload or {}).encode(),headers=headers,method='POST')
    with urllib.request.urlopen(req,timeout=25) as response:return json.load(response)
if __name__=='__main__':
    action=sys.argv[1]
    payload=json.loads(sys.stdin.read()) if action=='mail-result' else {}
    print(json.dumps(request(action,payload),ensure_ascii=False))
