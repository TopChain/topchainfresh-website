"""Public PNG names use the category, PT edition date, and category sequence."""
LABELS={'vocabulary':'Vocabulary','phrasal':'Phrasal verbs','idiom':'Idioms & slang','life':'Life phrases','grammar':'Grammar','quote':'Quote','small-talk':'Small talk'}
def assign_filenames(edition):
 counts={}
 for lesson in edition['lessons']:
  category=lesson['image'];counts[category]=counts.get(category,0)+1
  lesson['filename']=f"{LABELS[category]}_{edition['date']}_{counts[category]:02}.png"
 return edition
