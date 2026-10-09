"""Eight fixed Pacific refresh slots, preserving daylight-saving transitions."""
import zoneinfo
PACIFIC=zoneinfo.ZoneInfo('America/Los_Angeles')
def slot(now):
    local=now.astimezone(PACIFIC)
    return local.strftime('%Y-%m-%d')+f'T{local.hour//3*3:02d}:00'
def due(last,now):
    if not last:return True
    try:
        import datetime
        return slot(datetime.datetime.fromisoformat(last))!=slot(now)
    except (ValueError,TypeError):return True
