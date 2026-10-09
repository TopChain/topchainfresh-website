"""Classify provider-supplied regular sessions, including known lunch breaks."""
import datetime as dt
import zoneinfo

BREAKS={'Asia/Shanghai':('11:30','13:00'),'Asia/Tokyo':('11:30','12:30'),'Asia/Hong_Kong':('12:00','13:00')}

def classify(now, regular, timezone):
    start,end=regular.get('start'),regular.get('end')
    if not isinstance(start,(int,float)) or not isinstance(end,(int,float)) or end<=start:
        return 'Status unavailable'
    timestamp=now.timestamp()
    if start<=timestamp<end:
        local=now.astimezone(zoneinfo.ZoneInfo(timezone)).strftime('%H:%M')
        pause=BREAKS.get(timezone)
        if pause and pause[0]<=local<pause[1]:return 'Lunch break'
        return 'Trading now'
    if timestamp<start:return 'Not yet open'
    return 'Closed'

def analysis_gate(now, regular, timezone, bar_session):
    """Release only at the first Pacific three-hour refresh strictly after session close."""
    end=regular.get('end')
    if not isinstance(end,(int,float)):
        return {'analysisReady':False,'analysisStatus':'Exchange close time could not be verified.'}
    local_close=dt.datetime.fromtimestamp(end,zoneinfo.ZoneInfo(timezone))
    pacific_close=local_close.astimezone(zoneinfo.ZoneInfo('America/Los_Angeles'))
    first_hour=pacific_close.replace(hour=(pacific_close.hour//3)*3,minute=0,second=0,microsecond=0)+dt.timedelta(hours=3)
    gate={'analysisReady':False,'analysisEligibleAt':first_hour.astimezone(dt.timezone.utc).isoformat(),'sessionClosedAt':local_close.isoformat()}
    if classify(now,regular,timezone)!='Closed':
        gate['analysisStatus']='This market has not closed yet.'
    elif bar_session!=local_close.date().isoformat():
        gate['analysisStatus']='Awaiting the latest closed-session price data.'
    elif now<first_hour:
        gate['analysisStatus']='Market closed. Analysis is scheduled for the next scheduled three-hour update.'
    else:
        gate.update(analysisReady=True,analysisStatus='Closed-session technical observation available.')
    return gate
