import {createHash} from 'node:crypto';
import {digestDue} from './mail-schedule.mjs';
import {TOPICS,escape} from './core.mjs';
import {esc,https,a,eyebrow,note,card,button,title,p,designedEmail} from './email-design.mjs';
const home='https://www.topchainfresh.com/realfamily/';
const pacificDay=s=>new Date(s).toLocaleDateString('en-CA',{timeZone:'America/Los_Angeles'});
const time=s=>s?new Date(s).toLocaleString('en-US',{timeZone:'America/Los_Angeles',dateStyle:'medium',timeStyle:'short'})+' PT':'Unavailable';
const link=(title,url)=>{try{const u=new URL(url);return u.protocol==='https:'?`<a href="${escape(u.href)}">${escape(title)}</a>`:escape(title)}catch{return escape(title)}};
export function digestContent(data,topics,date,options={}){
 const sections=[];
 for(const topic of topics){
  if(!Object.hasOwn(TOPICS,topic))continue;
  let body='';
  if(topic==='news'){
   const eligible=r=>r.freeAccessVerified&&[date,pacificDay(Date.parse(date+'T12:00:00-07:00')-86400000)].includes(pacificDay(r.published));
   const world=Object.values(data.countries||{}).flat().filter(eligible).sort((a,b)=>Date.parse(b.published)-Date.parse(a.published));const seen=new Set();
   for(const [label,rows] of [['WORLD BRIEFING',world.slice(0,4)],['AI IN FOCUS',(data.ai||[]).filter(eligible).slice(0,3)]]){
    body+=eyebrow(label)+rows.filter(r=>{if(seen.has(r.url))return false;seen.add(r.url);return true}).map(r=>card(eyebrow(r.source)+title(r.title)+note(time(r.published))+a('Read the full report ↗',r.url))).join('');
   }
   if(!seen.size)body=p('No verified recent headlines are available.');
   body+=note('Freely accessible reports from major publishers. Open the news page for the complete country-by-country briefing.');
  }
  if(topic==='markets'){
   body=note('A snapshot with clear market status. These values are not necessarily final closing prices.')+Object.entries(data.markets||{}).slice(0,5).map(([name,m])=>card(eyebrow(m.provider||'MARKET SNAPSHOT')+title(name)+`<p style="font:normal 35px/1.2 Georgia,serif;margin:16px 0;color:#183e36">${esc(m.close==null?'Unavailable':Number(m.close).toLocaleString('en-US',{maximumFractionDigits:2}))}</p>`+p((m.change==null?'Change unavailable':Number(m.change).toFixed(2)+'%')+' · '+(m.marketStatus||'Status unavailable'))+note('Quote: '+(m.quoteAt||'Unavailable')+' · Local zone: '+(m.timezone||'Unavailable'))+note('Updated '+time(m.updated))+a('View source ↗',m.source),'#ae9a6b')).join('');
   body+=note('For reference only; not investment advice. See the market page for local session times and post-close analysis availability.');
  }
  if(topic==='health'){
   body=card(eyebrow('CARE FOR EVERY CHAPTER')+title('Small habits. A healthier everyday.')+p('Find food, nutrient and movement priorities for each of the ten age-and-sex profiles. The full guide explains when needs differ and when recommendations are shared.'));
   const rows=(data.research||[]).filter(r=>r.visible!==false&&r.discoveredDate===date).slice(0,3);
   body+=eyebrow('FROM THE RESEARCH DESK')+(rows.length?rows.map(r=>card(eyebrow(r.journal||'RESEARCH')+title(r.title)+note('Added '+date+' PT · Published '+r.date)+a('Read the original study ↗',r.url))).join(''):p('No new research additions today. Previous research remains available.'));
   body+=note('Research leads are not individualized medical advice. A single study does not establish a recommendation.');
  }
  if(topic==='recipes'){
   const recipes=(data.familyRecipes||[]);const indices=data.daily?.recipeIndices||[0,1];
   body=indices.map(index=>{const r=recipes[index];if(!r)return '';const photo=r.photo;const visual=photo&&https(photo.url)?`<img class="recipe-image" src="${esc(https(photo.url))}" alt="${esc(photo.alt||r.title)}" width="100%" style="width:100%;height:auto;display:block;border-radius:4px;margin-bottom:20px">`:'';
    return card(visual+eyebrow(r.cuisine+' · '+r.meal)+title(r.title)+p('Serves '+r.serves+' · Prep '+r.prep+' min · Cook '+r.cook+' min')+eyebrow('INGREDIENTS')+`<table role="presentation" width="100%" cellpadding="0" cellspacing="0">${r.ingredients.map(i=>`<tr><td style="padding:9px 0;border-bottom:1px solid #edf0e9;font:17px/1.5 Arial,sans-serif">${esc(i.name)}<br><span style="color:#65736c">${esc(i.amount)}</span></td></tr>`).join('')}</table>`+note(r.note||r.allergens||'')+button('Recipe & cooking tutorial',home+'#recipes')+(photo?note('Illustrative photograph · '+photo.author+' · '+photo.license)+a('Photo source',photo.source,'font-size:13px;'):''),'#c6aa87')}).join('');
   if(!body)body=p('Explore today’s six-serving main dishes and treats, with ingredients, steps and video links.');
  }
  if(topic==='english'){
   if(data.english?.date!==date)continue;
   const colors={vocabulary:'#b82c30',phrasal:'#ad5018',idiom:'#926a0c',life:'#1c5840',grammar:'#244890',quote:'#503773','small-talk':'#25272c',essay:'#183e36'},categories={vocabulary:'Vocabulary',phrasal:'Phrasal verbs',idiom:'Idioms & slang',life:'Life phrases',grammar:'Grammar',quote:'Quote','small-talk':'Small talk',essay:'Essay'};
   body=p((data.english.theme?'Today’s theme: '+data.english.theme+'. ':'')+'Connected language lessons, brought together in a short essay.')+data.english.lessons.map(l=>card(eyebrow(categories[l.image])+title(l.title)+p(l.meaning)+(l.image==='essay'?l.paragraphs.map(rows=>p(rows.join(' '))).join(''):'')+`<p style="font:18px/1.65 Arial,sans-serif;margin:16px 0;color:#354c40;border-left:3px solid ${colors[l.image]};padding-left:15px">${esc(l.example)}</p>`+a('Open & save the complete learning card ↗',home+'data/english-images/'+date+'/'+encodeURIComponent(l.filename||l.id+'.png')+'?revision='+(data.english.revision||1)),colors[l.image])).join('');
  }
  sections.push(eyebrow('REAL FAMILY / '+TOPICS[topic])+body+button('Explore '+TOPICS[topic],home+(topic==='english'?'?lesson-date='+date:'')+'#'+topic));
 }
 const selected=topics.filter(t=>Object.hasOwn(TOPICS,t));const headlines={news:'A world worth understanding.',markets:'The markets, in perspective.',health:'Live well, at every age.',recipes:'Good food. Shared together.',english:'Find the words for your world.'};
 return designedEmail({date,title:selected.length===1?headlines[selected[0]]:'Good things, all in one place.',kicker:selected.length===1?TOPICS[selected[0]]:'YOUR DAILY FAMILY DIGEST',body:sections.join(''),unsubscribe:options.unsubscribe,preview:options.preview});
}
export async function queueDigests(pool,data,now=new Date()){
 if(!digestDue(now))return 0;
 const date=pacificDay(now);const client=await pool.connect();let count=0;
 try{
  await client.query('BEGIN');await client.query("SELECT pg_advisory_xact_lock(hashtext('realfamily-digest'))");
  const {rows}=await client.query('SELECT s.email,s.topics,p.unsubscribe_url FROM realfamily.subscribers s JOIN realfamily.subscription_preferences p USING(email) WHERE s.active');
  for(const sub of rows){
   if(sub.topics.includes('english')&&data.english?.date!==date)continue;
   const key='digest-'+date+'-'+createHash('sha256').update(sub.email).digest('hex');
   const html=digestContent(data,sub.topics,date,{unsubscribe:sub.unsubscribe_url});
   const result=await client.query("INSERT INTO realfamily.mail_outbox(recipient,kind,subject,html,dedupe_key) VALUES($1,'digest',$2,$3,$4) ON CONFLICT(dedupe_key) DO NOTHING",[sub.email,'Real Family · Daily digest · '+date+' · PT',html,key]);count+=result.rowCount;
  }
  await client.query('COMMIT');return count;
 }catch(error){await client.query('ROLLBACK');throw error}finally{client.release()}
}
