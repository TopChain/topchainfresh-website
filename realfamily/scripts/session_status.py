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
