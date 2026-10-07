/* Render complete English lesson posters locally; no account or upload needed. */
const CARD_COLORS={red:'#b82c30',orange:'#ad5018',yellow:'#926a0c',green:'#1c5840',blue:'#244890',purple:'#503773',black:'#25272c'};
const cardFiles=new Map();
function currentEdition(){return SELECTED_EDITION||DATA.english}
function activeLessons(){const daily=currentEdition()?.lessons;return daily?.length?daily.map(l=>({...LESSONS.find(base=>base.image===l.image),...l})):LESSONS.map(l=>({...l,id:l.image}))}
function cardKey(lesson){return `${currentEdition()?.date||'preview'}-${lesson.image}-${lesson.title}`}
function wrapCardText(ctx,text,width){const lines=[];for(const paragraph of text.split('\n')){let line='';for(const word of paragraph.split(/\s+/)){const candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width>width&&line){lines.push(line);line=word}else line=candidate}lines.push(line)}return lines}
async function makeCardFile(lesson){const key=cardKey(lesson);if(cardFiles.has(key))return cardFiles.get(key);const promise=(async()=>{
 await document.fonts.ready;const canvas=document.createElement('canvas');canvas.width=1080;const ctx=canvas.getContext('2d');const width=928;const blocks=[
 {text:lesson.title,font:'bold 68px Georgia',line:82,gap:35},
 {text:'MEANING',font:'bold 24px Arial',line:32,gap:12},
 {text:lesson.meaning,font:'36px Arial',line:50,gap:28},
 {text:'IN CONTEXT',font:'bold 24px Arial',line:32,gap:12},
 {text:lesson.example,font:'36px Arial',line:50,gap:28},
 {text:'USAGE NOTE',font:'bold 24px Arial',line:32,gap:12},
 {text:lesson.notes,font:'30px Arial',line:43,gap:28},
 {text:'TRY THE CONVERSATION',font:'bold 24px Arial',line:32,gap:12},
 {text:lesson.conversation,font:'32px Arial',line:45,gap:28},
 {text:'YOUR TURN',font:'bold 24px Arial',line:32,gap:12},
 {text:lesson.exercise,font:'30px Arial',line:43,gap:35}];let height=640;for(const b of blocks){ctx.font=b.font;b.lines=wrapCardText(ctx,b.text,width);height+=b.lines.length*b.line+b.gap}canvas.height=height+160;
 ctx.fillStyle=CARD_COLORS[lesson.color];ctx.fillRect(0,0,1080,canvas.height);
 const img=new Image();img.src=`assets/${lesson.image}.png`;await img.decode();
 // The supplied cards contain illustrations above their bilingual text; use only the illustration region.
 const regions={vocabulary:[.07,.105,.86,.21],phrasal:[.07,.055,.86,.25],idiom:[.07,.06,.86,.27],'small-talk':[.16,.075,.68,.30],life:[0,0,1,.30],grammar:[0,0,1,.30],quote:[0,0,1,.32]};const r=regions[lesson.image];ctx.drawImage(img,img.naturalWidth*r[0],img.naturalHeight*r[1],img.naturalWidth*r[2],img.naturalHeight*r[3],76,105,928,420);
 ctx.fillStyle='#fff';ctx.font='bold 24px Arial';ctx.fillText('REAL FAMILY  /  EVERYDAY ENGLISH',76,62);ctx.font='bold 25px Arial';ctx.fillText(`${lesson.category.toUpperCase()}  ·  B2–C1`,76,586);let y=640;
 for(const b of blocks){ctx.font=b.font;ctx.fillStyle=b.font.includes('24px')?'#ffffffc9':'#fff';for(const line of b.lines){ctx.fillText(line,76,y);y+=b.line}y+=b.gap}
 ctx.fillStyle='#ffffffcc';ctx.font='24px Arial';ctx.fillText(`${currentEdition()?.date||'Preview'} · Pacific Time`,76,canvas.height-100);ctx.fillText('TopChainFresh.com/realfamily/',76,canvas.height-58);
 const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!blob)throw Error('Could not render image');const name=`real-family-${currentEdition()?.date||'lesson'}-${lesson.id}.png`;return new File([blob],name,{type:'image/png'});
 })();cardFiles.set(key,promise);promise.catch(()=>cardFiles.delete(key));return promise}
function downloadCard(file){const url=URL.createObjectURL(file);const a=document.createElement('a');a.href=url;a.download=file.name;document.body.append(a);a.click();a.remove();let preview=document.querySelector('#card-preview');if(preview)preview.remove();preview=document.createElement('dialog');preview.id='card-preview';preview.innerHTML='<button type="button" class="button" aria-label="Close card preview">Close</button><p class="fine">Your complete card · On mobile, touch and hold the image to save it.</p><img alt="Exported English learning card"><p><a class="button">Download PNG</a></p>';preview.querySelector('img').src=url;const link=preview.querySelector('a');link.href=url;link.download=file.name;preview.querySelector('button').onclick=()=>{preview.close();preview.remove();URL.revokeObjectURL(url)};document.body.append(preview);preview.showModal()}
async function exportLesson(button,action){const lesson=activeLessons().find(l=>l.id===button.dataset.value);if(!lesson)return;const label=button.textContent;button.disabled=true;button.textContent='Preparing…';const status=document.querySelector('#card-status');try{const file=await makeCardFile(lesson);if(action==='share-card'&&navigator.share&&navigator.canShare?.({files:[file]})){await navigator.share({files:[file],title:lesson.title,text:'A little English, every day — Real Family'});status.textContent='Card shared.'}else{downloadCard(file);status.textContent=action==='share-card'?'Image downloaded. Attach it in your preferred chat app.':'PNG image downloaded. On mobile, use your browser’s save options.'}}catch(error){if(error.name!=='AbortError')status.textContent='The card could not be saved. Please try again.'}finally{button.disabled=false;button.textContent=label}}
document.addEventListener('click',event=>{const button=event.target.closest('[data-action="share-card"],[data-action="save-card"]');if(button)exportLesson(button,button.dataset.action)});
function preloadCardExports(){for(const lesson of activeLessons())makeCardFile(lesson).catch(()=>{})}
