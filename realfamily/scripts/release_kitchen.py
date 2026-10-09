"""Immutable daily kitchen editions: ten themes, each with a new main and snack."""
import collections, datetime as dt, json, re, urllib.parse, zoneinfo
PACIFIC=zoneinfo.ZoneInfo('America/Los_Angeles')
CUISINES=('American','European','Japanese','Mediterranean','Chinese','Taiwanese','Hong Kong','Korean','Indian','Seasonal')
def normalized(text):return re.sub(r'[^a-z0-9]','',text.lower())
def history(root,exclude=None):
    rows=json.loads((root/'recipes.js').read_text().split('=',1)[1].strip().rstrip(';'))
    for folder in ('recipes-archive','recipes-staged'):
        for file in (root/'data'/folder).glob('*.json'):
            if file.stem!=exclude:rows.extend(json.loads(file.read_text())['recipes'])
    return rows
def validate(root,edition,photos=True):
    dt.date.fromisoformat(edition['date'])
    rows=edition['recipes']
    assert len(rows)==20,'Twenty recipes required'
    assert collections.Counter((r['cuisine'],r['meal']) for r in rows)==collections.Counter((c,m) for c in CUISINES for m in ('Main','Snack')),'Each theme needs one main and one snack'
    used={normalized(r['title']) for r in history(root,edition['date'])}
    for r in rows:
        assert r['serves']==6,'Six servings required'
        assert isinstance(r['prep'],int) and 0<r['prep']<=180
        assert isinstance(r['cook'],int) and 0<=r['cook']<=240
        key=normalized(r['title']);assert key and key not in used,'Repeated recipe title';used.add(key)
        assert 5<=len(r['ingredients'])<=20
        for item in r['ingredients']:
            assert isinstance(item['name'],str) and item['name'].strip()
            assert isinstance(item['amount'],str) and re.search(r'\d',item['amount']),'Ingredient quantity missing'
        assert 5<=len(r['steps'])<=10 and all(isinstance(s,str) and len(s.split())>=9 for s in r['steps']),'Detailed method required'
        for key in ('allergens','note','storage'):assert isinstance(r.get(key),str) and r[key].strip(),key
        assert not re.search(r'\b(wine|beer|brandy|sake|mirin|rum|alcohol)\b',' '.join(i['name'] for i in r['ingredients']),re.I),'Use alcohol-free ingredients'
        if photos:
            p=r['photo'];assert p.get('author') and p.get('license') and p.get('alt')
            assert urllib.parse.urlsplit(p['url']).hostname in ('upload.wikimedia.org','thumb.wikimedia.org')
            assert p['source'].startswith('https://commons.wikimedia.org/wiki/File:')
            assert p['licenseUrl'].startswith(('https://creativecommons.org/','https://commons.wikimedia.org/'))
            assert r['videoSearch'].startswith('https://www.youtube.com/results?search_query=')
    assert edition.get('editorialApproved') is True,'Editorial approval required'
    return True
def release(root,now):
    date=now.astimezone(PACIFIC).date().isoformat()
    staged=root/'data/recipes-staged'/f'{date}.json';archive=root/'data/recipes-archive'/f'{date}.json'
    if archive.exists() or not staged.exists():return False
    edition=json.loads(staged.read_text());assert edition['date']==date
    validate(root,edition)
    edition['published']=now.isoformat();edition['recipeIndices']=list(range(20))
    archive.parent.mkdir(parents=True,exist_ok=True)
    archive.write_text(json.dumps(edition,ensure_ascii=False,indent=2)+'\n');staged.unlink()
    return True
