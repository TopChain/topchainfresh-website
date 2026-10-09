import {test} from 'node:test';import assert from 'node:assert/strict';import {pacificClock,plan} from './plan.mjs';
test('7:30 AM follows Pacific daylight and standard time',()=>{
 for(const date of ['2026-10-09T14:29:00Z','2026-12-09T15:29:00Z'])assert.equal(pacificClock(new Date(date)).due,false);
 for(const date of ['2026-10-09T14:30:00Z','2026-12-09T15:30:00Z'])assert.equal(pacificClock(new Date(date)).due,true);
 assert.equal(pacificClock(new Date('2026-10-09T06:30:00Z')).date,'2026-10-08');
});
test('incomplete or wrong-day editions never produce a send plan',()=>{
 assert.throws(()=>plan({date:'2026-10-08',lessons:[]},[],'2026-10-09'));
 assert.throws(()=>plan({date:'2026-10-09',lessons:Array(10).fill({id:'2026-10-09-1',image:'vocabulary',filename:'../../file'})},[],'2026-10-09'));
});

test('Essay joins its own verified destination without changing the ten existing routes',async()=>{
 const {readFile}=await import('node:fs/promises');const {CATEGORIES}=await import('./plan.mjs');
 const edition=JSON.parse(await readFile(new URL('../../data/english-archive/2026-10-09.json',import.meta.url)));
 const routes=Object.values(CATEGORIES).map((category,i)=>({category,groupName:category==='Essay'?'Essay@Family':category+'@Family',jid:`100-${i+1}@g.us`}));
 const jobs=plan(edition,routes,edition.date);assert.equal(jobs.length,11);assert.equal(jobs.find(j=>j.lesson.image==='essay').route.groupName,'Essay@Family');
 assert.throws(()=>plan(edition,routes.filter(r=>r.category!=='Essay'),edition.date));
 assert.throws(()=>plan(edition,routes.map(r=>r.category==='Essay'?{...r,jid:routes[0].jid}:r),edition.date));
});
