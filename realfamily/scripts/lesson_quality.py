"""Structural checks supplement the editorial review of topic relevance."""
GENERIC=('Use this pattern when the meaning fits the situation.', 'Make this your own: write one example from your life', 'I kept this reflection in mind while deciding how to respond.')
def validate_lesson(lesson):
    if lesson['image']=='essay':
        paragraphs=lesson.get('paragraphs',[])
        assert len(paragraphs)==4, 'Essay needs four paragraphs'
        for rows,low,high in zip(paragraphs,[1,2,2,1],[2,3,3,2]):
            assert isinstance(rows,list) and low<=len(rows)<=high and all(isinstance(t,str) and t.strip() for t in rows), 'Wrong essay paragraph sentence counts'
        assert 8<=sum(map(len,paragraphs))<=10, 'Essay needs 8-10 sentences'
        assert 4<=len(lesson.get('connections',[]))<=10, 'Essay needs selected vocabulary, phrasal verb, idiom and grammar connections'
        assert lesson.get('structure') and lesson.get('exercise'), 'Essay needs structure guidance and practice'
        return True
    turns=lesson['conversation'].replace('\\n','\n').splitlines()
    expected=8 if lesson['image']=='small-talk' else 4
    assert len(turns)==expected, f"{lesson['title']}: expected {expected} dialogue turns"
    assert all(turn.startswith(('A:','B:')[i%2]) and turn[2:].strip() for i,turn in enumerate(turns)), 'Dialogue must alternate A/B with nonempty replies'
    for field in ('meaning','example','notes','exercise'):
        assert isinstance(lesson.get(field),str) and lesson[field].strip(), 'Missing '+field
        assert not any(template.casefold() in lesson[field].casefold() for template in GENERIC), 'Generic teaching template in '+field
    if lesson['image']=='vocabulary':
        assert isinstance(lesson.get('ipa'),str) and lesson['ipa'].startswith('/') and lesson['ipa'].endswith('/') and len(lesson['ipa'])>2, 'Vocabulary needs American IPA'
        assert lesson.get('ipaAccent')=='en-US', 'Use American pronunciation only'
    if lesson['image']=='quote':
        assert 'real family' not in lesson['notes'].casefold(), 'Brand mention in Quote usage note'
        assert lesson['title'] in lesson['example'] and lesson['title'] in lesson['conversation'], 'Quote must appear in example and conversation'
    return True
