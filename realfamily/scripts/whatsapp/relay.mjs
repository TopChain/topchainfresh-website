import makeWASocket,{useMultiFileAuthState,Browsers} from '@whiskeysockets/baileys';
import pino from 'pino';import QRCode from 'qrcode';import http from 'node:http';
import {mkdtemp,readFile,writeFile,readdir,rm,mkdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';import {join,resolve} from 'node:path';
import {randomBytes,createCipheriv,createDecipheriv,createHash} from 'node:crypto';
import {pacificClock,plan} from './plan.mjs';
// User confirmed this exact destination after removing the duplicate name.
const ESSAY_GROUP_NAME='Essay@Family';
const pairing=process.argv.includes('--pair');const root=resolve(import.meta.dirname,'../..');
const key=Buffer.from(process.env.WHATSAPP_STATE_KEY||'','base64');if(key.length!==32)throw Error('Private encryption key required');
async function api(action,body){const r=await fetch(process.env.SUBSCRIPTION_ENDPOINT+'?action='+action,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+process.env.MAILER_SECRET},body:JSON.stringify(body),signal:AbortSignal.timeout(25000)});if(!r.ok)throw Error('Private state request failed');return r.json()}
function seal(value){const iv=randomBytes(12),c=createCipheriv('aes-256-gcm',key,iv);c.setAAD(Buffer.from('real-family-whatsapp-v1'));const data=Buffer.concat([c.update(JSON.stringify(value)),c.final()]);return Buffer.concat([iv,c.getAuthTag(),data]).toString('base64')}
function unseal(text){const b=Buffer.from(text,'base64'),d=createDecipheriv('aes-256-gcm',key,b.subarray(0,12));d.setAAD(Buffer.from('real-family-whatsapp-v1'));d.setAuthTag(b.subarray(12,28));return JSON.parse(Buffer.concat([d.update(b.subarray(28)),d.final()]).toString())}
async function get(name){const r=await api('wa-state-get',{name});return r.encrypted?unseal(r.encrypted):null}
async function put(name,value){await api('wa-state-put',{name,encrypted:seal(value)})}
const folder=await mkdtemp(join(tmpdir(),'realfamily-wa-'));const previous=await get('auth');
if(previous)for(const [file,content] of Object.entries(previous)){if(!/^[\w.@-]+\.json$/.test(file)||typeof content!=='string')throw Error('Invalid session file');JSON.parse(content);await writeFile(join(folder,file),content,{mode:0o600})}
if(!pairing&&!previous)throw Error('WhatsApp needs phone linking');
const {state,saveCreds}=await useMultiFileAuthState(folder);let saveChain=Promise.resolve();
async function save(){const files={};for(const file of await readdir(folder))if(file.endsWith('.json'))files[file]=await readFile(join(folder,file),'utf8');await put('auth',files)}
function scheduleSave(operation=async()=>{}){saveChain=saveChain.then(async()=>{await operation();await save()});return saveChain}
const originalSet=state.keys.set.bind(state.keys);state.keys.set=data=>scheduleSave(()=>originalSet(data));
let qr='',status='Preparing secure connection',server;
if(pairing){
 server=http.createServer(async(req,res)=>{res.setHeader('Cache-Control','no-store');res.setHeader('Content-Type','text/html; charset=utf-8');res.end(`<html><meta http-equiv="refresh" content="10"><title>Real Family WhatsApp linking</title><body style="font:22px system-ui;background:#f6f5ef;color:#183e36;padding:40px;text-align:center"><h1>Real Family</h1><p>${status}</p>${qr?'<img width="320" src="'+await QRCode.toDataURL(qr)+'">':''}<p>WhatsApp → Settings → Linked devices → Link a device</p><p>Daily cards: 7:30 AM PT</p></body></html>`)});server.listen(8770,'127.0.0.1');console.log('Phone linking page ready at http://127.0.0.1:8770');
}
let socket;let done=false;let success=false;let reconnects=0;let stage='connecting';
const timeout=setTimeout(()=>{console.error('Connection deadline reached; no unconfirmed card is resent.');process.exit(1)},pairing?600000:180000);
async function complete(){
 if(pairing){
  stage='loading group settings';const routing=JSON.parse(await readFile(join(root,'data/whatsapp-routing.private.json'),'utf8'));
  stage='fetching groups';const groups=Object.values(await socket.groupFetchAllParticipating());
  await writeFile('/tmp/realfamily-whatsapp-private/group-check.json',JSON.stringify(routing.routes.map(route=>({category:route.category,expected:route.groupName,pinnedCurrent:groups.find(g=>g.id===route.jid)?.subject||null,matches:groups.filter(g=>g.subject===route.groupName).length,similar:groups.filter(g=>g.subject.toLowerCase().includes(route.groupName.split('@')[0].toLowerCase())).map(g=>({name:g.subject,jid:g.id,participants:g.participants.length,created:g.creation}))}))),{mode:0o600});
  stage='matching destinations';const routes=routing.routes.map(route=>{const matches=groups.filter(g=>g.subject===route.groupName&&(!route.jid||g.id===route.jid));if(matches.length!==1)throw Error('A destination is missing or ambiguous');return {...route,jid:matches[0].id}});
  stage='saving verified routes';await put('routes',routes);await scheduleSave();
  // Desktop deliveries are verified locally. Reserve their original IDs so a cloud
  // cutover cannot repeat today's already-delivered cards; do not invent server IDs.
  stage='seeding previous deliveries';const past=JSON.parse(await readFile(join(root,'data/whatsapp-send-log.private.json'),'utf8'));
  for(const record of past.deliveries||[])if(record.verified&&record.status==='sent'){
   const route=routes.find(r=>r.category===record.category);if(!route)continue;
   for(const lessonId of record.lessonIds||[]){const claim=await api('wa-claim',{lessonId,destinationHash:createHash('sha256').update(route.jid).digest('hex')});if(claim.allowed)await api('wa-result',{lessonId,status:'uncertain'})}
  }
  qr='';status='Connected. Destination groups verified. You can close this page.';success=true;console.log('Phone linked; all selected groups verified. No cards sent during setup.');socket.end(undefined);return;
 }
 stage='loading encrypted routes';const verifiedRoutes=await get('routes');if(!verifiedRoutes)throw Error('Group routes are not verified');
 stage='fetching current groups';const activeGroups=await socket.groupFetchAllParticipating();
 if(!verifiedRoutes.some(r=>r.category==='Essay')){
  stage='matching Essay@Family';const matches=Object.values(activeGroups).filter(g=>ESSAY_GROUP_NAME&&g.subject===ESSAY_GROUP_NAME);
  console.log('Essay@Family exact matches: '+matches.length);
  if(matches.length===1){
   verifiedRoutes.push({category:'Essay',groupName:ESSAY_GROUP_NAME,jid:matches[0].id});
   await put('routes',verifiedRoutes);console.log('Essay@Family verified and added to encrypted cloud routes.');
  }else if(process.env.WHATSAPP_VERIFY_ONLY==='true'){throw Error('Essay@Family is missing or ambiguous')}
  else console.log('Essay destination needs selection; the ten existing cards remain enabled.');
 }
 stage='checking eight destinations';if(![7,8].includes(verifiedRoutes.length)||verifiedRoutes.some(r=>activeGroups[r.jid]?.subject!==r.groupName))throw Error('Verified destination changed or unavailable');
 if(process.env.WHATSAPP_VERIFY_ONLY==='true'){console.log('Cloud session restored; all '+verifiedRoutes.length+' selected groups verified. Verification only: zero cards sent.');return}
 const clock=pacificClock();if(!clock.due){console.log('Before 7:30 AM PT; no cards sent.');return}
 const edition=JSON.parse(await readFile(join(root,'data/english-archive',clock.date+'.json'),'utf8'));
 const routes=verifiedRoutes;const deliveryEdition=routes.some(r=>r.category==='Essay')?edition:{...edition,lessons:edition.lessons.filter(l=>l.image!=='essay')};const jobs=plan(deliveryEdition,routes,clock.date);
 // Validate every image before claiming any delivery.
 for(const job of jobs){job.png=await readFile(join(root,'data/english-images',clock.date,job.lesson.filename));if(job.png.toString('hex',0,8)!=='89504e470d0a1a0a'||job.png.readUInt32BE(16)!==(job.lesson.image==='essay'?1434:660)||job.png.readUInt32BE(20)!==(job.lesson.image==='essay'?660:1434))throw Error('Invalid PNG')}
 for(const {lesson,route,png} of jobs){
  const claimed=await api('wa-claim',{lessonId:lesson.id,destinationHash:createHash('sha256').update(route.jid).digest('hex')});if(!claimed.allowed)continue;
  try{const msg=await socket.sendMessage(route.jid,{image:png,caption:`${route.category} · ${edition.date} · PT\n${lesson.title}`,fileName:lesson.filename});if(!msg?.key?.id)throw Error('Send result unknown');await scheduleSave();await api('wa-result',{lessonId:lesson.id,status:'sent',messageId:msg.key.id})}
  catch{await api('wa-result',{lessonId:lesson.id,status:'uncertain'});throw Error('A send is uncertain; review required before retry')}
 }
 console.log('Daily relay finished; stored message IDs indicate server acceptance, not recipient read status.');
}
function connect(){
 socket=makeWASocket({auth:state,logger:pino({level:'silent'}),syncFullHistory:false,shouldSyncHistoryMessage:()=>false,markOnlineOnConnect:false,browser:Browsers.macOS('Chrome'),qrTimeout:120000});
 socket.ev.on('creds.update',async()=>{try{await scheduleSave(saveCreds)}catch{console.error('Session persistence failed');process.exit(1)}});
 socket.ev.on('connection.update',async update=>{
  if(update.qr&&pairing){qr=update.qr;status='Scan this code with your phone. Never share this screen.';await QRCode.toFile('/tmp/realfamily-whatsapp-private/link-device.png',qr,{width:480,margin:4});const {chmod}=await import('node:fs/promises');await chmod('/tmp/realfamily-whatsapp-private/link-device.png',0o600);console.log('Private phone-linking image refreshed.')}
  if(update.connection==='close'&&!done){const code=update.lastDisconnect?.error?.output?.statusCode;if(code===515||pairing&&[408,428].includes(code)&&reconnects++<3)connect();else{console.error('WhatsApp disconnected; status '+(code||'unknown')+'; phone linking or review required.');process.exit(1)}}
  if(update.connection==='open'&&!done){done=true;try{await complete();await saveChain;if(!pairing){clearTimeout(timeout);await socket.end(undefined);await saveChain;process.exit(0)}else if(success)clearTimeout(timeout)}catch(error){if(pairing)await writeFile('/tmp/realfamily-whatsapp-private/failure.json',JSON.stringify({stage,error:String(error?.message||'unknown')}),{mode:0o600});status='Setup could not verify all destinations. Please return to Codex.';console.error('Relay failed safely at '+stage+'; no private account details printed.');process.exit(1)}}
 });
}
connect();
