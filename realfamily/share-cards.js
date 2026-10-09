/* Render complete English lesson posters locally; no account or upload needed. */
const CARD_COLORS={red:'#b82c30',orange:'#ad5018',yellow:'#926a0c',green:'#1c5840',blue:'#244890',purple:'#503773',black:'#25272c'};
const cardFiles=new Map();
function currentEdition(){return SELECTED_EDITION||DATA.english}
function activeLessons(){const daily=currentEdition()?.lessons;return daily?.length?daily.map(l=>({...LESSONS.find(base=>base.image===l.image),...l,category:l.image==='essay'?'Essay':LESSONS.find(base=>base.image===l.image)?.category,color:l.image==='essay'?'green':LESSONS.find(base=>base.image===l.image)?.color})):LESSONS.map(l=>({...l,id:l.image}))}
function cardKey(lesson,edition=currentEdition()){return `${edition?.date||'preview'}-${lesson.image}-${lesson.title}-${edition?.revision||1}`}
function wrapCardText(ctx,text,width){const lines=[];for(const paragraph of text.split('\n')){let line='';for(const word of paragraph.split(/\s+/)){const candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width>width&&line){lines.push(line);line=word}else line=candidate}lines.push(line)}return lines}
function cardFilename(lesson){return lesson.filename||lesson.id+'.png'}
async function makeCardFile(lesson,edition=currentEdition()){const key=cardKey(lesson,edition);if(cardFiles.has(key))return cardFiles.get(key);const promise=(async()=>{const date=edition?.date;if(!date||!lesson.id)throw Error('No dated card available');const response=await fetch(`data/english-images/${date}/${encodeURIComponent(cardFilename(lesson))}?revision=${edition?.revision||1}`,{cache:'no-cache'});if(!response.ok)throw Error('Card image unavailable');const blob=await response.blob();if(!blob.type.startsWith('image/'))throw Error('Invalid card image');return new File([blob],cardFilename(lesson),{type:'image/png'})})();cardFiles.set(key,promise);promise.catch(()=>cardFiles.delete(key));return promise}

// Store the original PNG bytes in one UTF-8 ZIP, with no external service or library.
function cardCRC32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0)}return (crc^0xffffffff)>>>0}
async function makeCardArchive(files,date){
 if(![10,11].includes(files.length)||new Set(files.map(f=>f.name)).size!==files.length)throw Error('Ten unique cards required');
 const parts=[],directory=[];let offset=0,directorySize=0;const encode=new TextEncoder(),[year,month,day]=date.split('-').map(Number),stamp=((year-1980)<<9)|(month<<5)|day;
 for(const file of files){
  const name=encode.encode(file.name),bytes=new Uint8Array(await file.arrayBuffer()),crc=cardCRC32(bytes);
  if(bytes.length<24||bytes[0]!==137||bytes[1]!==80||bytes[2]!==78||bytes[3]!==71)throw Error('Invalid PNG card');
  const local=new Uint8Array(30),l=new DataView(local.buffer);l.setUint32(0,0x04034b50,true);l.setUint16(4,20,true);l.setUint16(6,0x0800,true);l.setUint16(12,stamp,true);l.setUint32(14,crc,true);l.setUint32(18,bytes.length,true);l.setUint32(22,bytes.length,true);l.setUint16(26,name.length,true);
  const central=new Uint8Array(46),c=new DataView(central.buffer);c.setUint32(0,0x02014b50,true);c.setUint16(4,20,true);c.setUint16(6,20,true);c.setUint16(8,0x0800,true);c.setUint16(14,stamp,true);c.setUint32(16,crc,true);c.setUint32(20,bytes.length,true);c.setUint32(24,bytes.length,true);c.setUint16(28,name.length,true);c.setUint32(42,offset,true);
  parts.push(local,name,bytes);directory.push(central,name);offset+=local.length+name.length+bytes.length;directorySize+=central.length+name.length;
 }
 const end=new Uint8Array(22),e=new DataView(end.buffer);e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);e.setUint32(12,directorySize,true);e.setUint32(16,offset,true);
 return new File([...parts,...directory,end],`Real Family_${date}.zip`,{type:'application/zip'});
}
async function downloadAllCards(button){
 const edition=currentEdition(),label=button.textContent,status=document.querySelector('#bulk-card-status');button.disabled=true;button.textContent=`Preparing ${edition.lessons.length} cards…`;
 try{
  if(!edition?.date||![10,11].includes(edition.lessons?.length))throw Error('Incomplete edition');
  const files=await Promise.all(edition.lessons.map(l=>makeCardFile(l,edition))),archive=await makeCardArchive(files,edition.date),url=URL.createObjectURL(archive),link=document.createElement('a');
  link.href=url;link.download=archive.name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
  if(status)status.textContent=`Your ${edition.date} ZIP is ready: all ${files.length} original PNG cards. Open the ZIP to extract the images.`;
 }catch{if(status)status.textContent='The complete set could not be downloaded. Please try again; all cards must be available.'}
 finally{button.disabled=false;button.textContent=label}
}
document.addEventListener('click',event=>{const button=event.target.closest('[data-download-all]');if(button)downloadAllCards(button)});

function downloadCard(file){const url=URL.createObjectURL(file);const a=document.createElement('a');a.href=url;a.download=file.name;document.body.append(a);a.click();a.remove();let preview=document.querySelector('#card-preview');if(preview)preview.remove();preview=document.createElement('dialog');preview.id='card-preview';preview.innerHTML='<button type="button" class="button" aria-label="Close card preview">Close</button><p class="fine">Your complete card · On mobile, touch and hold the image to save it.</p><img alt="Exported English learning card"><p><a class="button">Download PNG</a></p>';preview.querySelector('img').src=url;const link=preview.querySelector('a');link.href=url;link.download=file.name;preview.querySelector('button').onclick=()=>{preview.close();preview.remove();URL.revokeObjectURL(url)};document.body.append(preview);preview.showModal()}
async function exportLesson(button,action){const lesson=activeLessons().find(l=>l.id===button.dataset.value);if(!lesson)return;const label=button.textContent;button.disabled=true;button.textContent='Preparing…';const status=document.querySelector('#card-status');try{const file=await makeCardFile(lesson);if(action==='share-card'&&navigator.share&&navigator.canShare?.({files:[file]})){await navigator.share({files:[file],title:lesson.title,text:'A little English, every day — Real Family'});status.textContent='Card shared.'}else{downloadCard(file);status.textContent=action==='share-card'?'Image downloaded. Attach it in your preferred chat app.':'PNG image downloaded. On mobile, use your browser’s save options.'}}catch(error){if(error.name!=='AbortError')status.textContent='The card could not be saved. Please try again.'}finally{button.disabled=false;button.textContent=label}}
document.addEventListener('click',event=>{const button=event.target.closest('[data-action="share-card"],[data-action="save-card"]');if(button)exportLesson(button,button.dataset.action)});
function preloadCardExports(){for(const lesson of activeLessons())makeCardFile(lesson).catch(()=>{})}

// Printing uses separate white-paper vector files; screen/share PNGs remain unchanged.
async function printLessonCards(button,all=false){
 const edition=currentEdition(),lessons=all?activeLessons():activeLessons().filter(l=>l.id===button.dataset.value),label=button.textContent,status=document.querySelector(all?'#bulk-card-status':'#card-status');
 if(!edition?.date||!lessons.length)return;
 const popup=window.open('','_blank');if(!popup){if(status)status.textContent='Allow the print window in your browser, then try again.';return;}
 button.disabled=true;button.textContent='Preparing print…';
 const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const imageURL=l=>new URL(`data/english-print/${edition.date}/${encodeURIComponent(cardFilename(l).replace(/\.png$/,'.svg'))}?revision=${edition.revision||1}&print=1`,location.href).href;
 const regular=lessons.filter(l=>l.image!=='essay'),essay=lessons.filter(l=>l.image==='essay'),pages=[];
 const card=l=>`<img src="${safe(imageURL(l))}" alt="${safe(l.title)} — ink-saving print card">`;
 for(let i=0;i<regular.length;i+=2)pages.push(`<section class="sheet ${all?'pair':'single'}">${regular.slice(i,i+2).map(card).join('')}</section>`);
 for(const l of essay)pages.push(`<section class="sheet essay">${card(l)}</section>`);
 popup.document.write(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Everyday English · ${safe(edition.date)} · Print</title><style>
 @page{size:Letter portrait;margin:0.35in}@page essay{size:Letter landscape;margin:0.35in}
 *{box-sizing:border-box}body{margin:0;background:#eee;color:#292929;font:16px/1.5 Arial,sans-serif}.toolbar{position:sticky;top:0;background:#f6f1e8;padding:16px 24px;border-bottom:1px solid #ccc}.toolbar button{padding:8px 16px;margin-right:10px;background:white;border:1px solid #777;border-radius:5px;color:#292929;cursor:pointer}.toolbar p{margin:8px 0 0}main{padding:20px}.sheet{background:white;margin:0 auto 24px;padding:12px;max-width:780px;display:flex;align-items:center;justify-content:center;gap:12px}.sheet img{display:block;width:calc(50% - 6px);height:auto}.single img{width:60%}.essay{max-width:1100px}.essay img{width:100%}
 @media print{body,main{margin:0;padding:0;background:white}.toolbar{display:none}.sheet{margin:0;padding:0;max-width:none;height:10.28in;gap:0.18in;break-inside:avoid;break-after:page}.sheet:last-child{break-after:auto}.pair img{width:3.81in;height:auto;max-height:10.28in;object-fit:contain}.single img{height:10.28in;width:auto;max-width:100%;object-fit:contain}.essay{page:essay;height:7.78in}.essay img{width:10.28in;height:auto;max-height:7.78in;object-fit:contain}}
 </style></head><body><div class="toolbar"><button id="print-now" disabled>Print / Save as PDF</button><button id="close-print">Close</button><p id="print-status" role="status">Loading ${lessons.length} ink-saving cards…</p><p>Letter paper · ${all?'Two portrait cards per page; Essay alone on the last landscape page.':'One card on one page.'} White interiors and thin category borders. Choose Letter paper and disable browser headers and footers.</p></div><main>${pages.join('')}</main></body></html>`);popup.document.close();
 popup.document.querySelector('#close-print').onclick=()=>popup.close();const printButton=popup.document.querySelector('#print-now');printButton.onclick=()=>{popup.focus();popup.print()};
 try{
  await Promise.all([...popup.document.images].map(img=>new Promise((resolve,reject)=>{if(img.complete)return img.naturalWidth?resolve():reject(Error('Missing print file'));img.onload=resolve;img.onerror=reject})));
  printButton.disabled=false;popup.document.querySelector('#print-status').textContent=`Ready: ${lessons.length} complete ink-saving card${lessons.length===1?'':'s'}.`;
  if(status)status.textContent='Ink-saving print layout opened. Use Print / Save as PDF in the new window.';
  popup.focus();popup.print();
 }catch{if(!popup.closed)popup.document.querySelector('#print-status').textContent='Some print cards could not load. Close this window and try again; no partial set will be printed.';if(status)status.textContent='Print cards could not load. Please try again.';}
 finally{button.disabled=false;button.textContent=label}
}
document.addEventListener('click',event=>{const button=event.target.closest('[data-print-all],[data-action="print-card"]');if(button)printLessonCards(button,button.hasAttribute('data-print-all'))});
