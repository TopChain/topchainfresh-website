"""Cloud Gmail relay; secrets come from the runner, never from public files."""
import base64,email.policy,json,os,urllib.parse,urllib.request
from email.message import EmailMessage
from subscription_mail_queue import request as queue

def http(url, data=None, headers=None):
    req=urllib.request.Request(url,data=data,headers=headers or {})
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)

def token():
    body=urllib.parse.urlencode({'client_id':os.environ['GMAIL_CLIENT_ID'],'client_secret':os.environ['GMAIL_CLIENT_SECRET'],'refresh_token':os.environ['GMAIL_REFRESH_TOKEN'],'grant_type':'refresh_token'}).encode()
    return http('https://oauth2.googleapis.com/token',body,{'Content-Type':'application/x-www-form-urlencoded'})['access_token']

def api(access, path, body=None):
    return http('https://gmail.googleapis.com/gmail/v1/users/me/'+path,json.dumps(body).encode() if body is not None else None,{'Authorization':'Bearer '+access,'Content-Type':'application/json'})

def find_sent(access,job):
    # Search is a candidate filter: verify exact decoded headers before acknowledging.
    query='in:sent to:'+job['recipient']+' subject:"'+job['subject'].replace('"','')+'"'
    result=api(access,'messages?'+urllib.parse.urlencode({'q':query,'maxResults':100}))
    if result.get('nextPageToken'):raise RuntimeError('Sent search requires pagination; no blind send')
    for candidate in result.get('messages',[]):
        msg=api(access,'messages/'+candidate['id']+'?format=metadata&metadataHeaders=Subject&metadataHeaders=To')
        headers={h['name'].lower():h['value'] for h in msg.get('payload',{}).get('headers',[])}
        from email.utils import getaddresses
        recipients={address.lower() for _,address in getaddresses([headers.get('to','')])}
        if headers.get('subject')==job['subject'] and job['recipient'].lower() in recipients:return candidate['id']
    return None

def mime(job):
    message=EmailMessage(policy=email.policy.SMTP)
    message['From']='Real Family <topchainfresh@gmail.com>'
    message['To']=job['recipient'];message['Subject']=job['subject']
    message.set_content(job['html'],subtype='html',charset='utf-8')
    return base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip('=')

def deliver(access,job,lease):
    result={'id':job['id'],'lease':lease,'status':'uncertain'}
    try:
        message_id=find_sent(access,job)
        if not message_id and job.get('prior_status')=='uncertain':
            # An ambiguous send may not yet be indexed. Do not repeat it automatically.
            return False
        if not message_id:
            permitted=queue('mail-check',{'id':job['id'],'lease':lease})
            if not permitted.get('allowed'):
                result['status']='pending';return False
            message_id=api(access,'messages/send',{'raw':mime(job)}).get('id')
            if not message_id:raise RuntimeError('Gmail did not confirm a message ID')
        result.update(status='sent',messageId=message_id)
        return True
    finally:
        queue('mail-result',result)

def main():
    required=('GMAIL_CLIENT_ID','GMAIL_CLIENT_SECRET','GMAIL_REFRESH_TOKEN','MAILER_SECRET','SUBSCRIPTION_ENDPOINT')
    if not all(os.environ.get(name) for name in required):raise RuntimeError('Cloud mail credentials are incomplete')
    access=token()
    profile=api(access,'profile')
    if profile.get('emailAddress','').lower()!='topchainfresh@gmail.com':raise RuntimeError('Wrong Gmail sender account')
    queue('mail-digests');claimed=queue('mail-claim');sent=0;unresolved=0
    for job in claimed['jobs']:
        try:
            if deliver(access,job,claimed['lease']):sent+=1
            else:unresolved+=1
        except Exception:
            unresolved+=1  # No recipient, token, HTML, or provider error appears in public logs.
    print(f'Cloud mail: {sent} confirmed; {unresolved} require retry or review.')
    if unresolved:raise RuntimeError('Some mail jobs were not confirmed; inspect the private queue')

if __name__=='__main__':main()
