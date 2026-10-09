export const CATEGORIES={vocabulary:'Vocabulary',phrasal:'Phrasal verbs',idiom:'Idioms & slang',life:'Life phrases',grammar:'Grammar',quote:'Quote','small-talk':'Small talk',essay:'Essay'};
export function pacificClock(now=new Date()){
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(p=>[p.type,p.value]));
 return {date:`${parts.year}-${parts.month}-${parts.day}`,due:Number(parts.hour)*60+Number(parts.minute)>=450};
}
export function plan(edition,routes,date){
 if(edition.date!==date||![10,11].includes(edition.lessons?.length))throw Error('Today must have ten complete cards');
 const counts={};const ids=new Set();
 const jobs=edition.lessons.map(l=>{
  const category=CATEGORIES[l.image];const route=routes.find(r=>r.category===category);
  if(!category||!route||!/^\d+(-\d+)?@g\.us$/.test(route.jid)||!l.id.startsWith(date+'-')||ids.has(l.id)||!l.filename||/[\/\\]/.test(l.filename))throw Error('Invalid lesson or verified group route');
  ids.add(l.id);counts[l.image]=(counts[l.image]||0)+1;return {lesson:l,route};
 });
 for(const k of Object.keys(CATEGORIES).filter(k=>k!=='essay'||edition.lessons.length===11))if(counts[k]!==(['vocabulary','phrasal','idiom'].includes(k)?2:1))throw Error('Incorrect daily category count');
 if(new Set(routes.map(r=>r.jid)).size!==routes.length||![7,8].includes(routes.length))throw Error('Distinct verified groups required');
 return jobs;
}
