// Approved flat comic style; only bounded drawing instructions, never executable model output.
const fs=require('node:fs'),path=require('node:path');
const sharp=require(process.env.REAL_FAMILY_SHARP||'/Users/jr/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const ink='#263e38',esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const props={
 check:'<rect width="84" height="64" rx="9" fill="white"/><path d="M20 33l15 14 30-32" fill="none" stroke="#4e9186"/>',
 question:'<path d="M0 0h90v65H35L15 82V65H0Z" fill="white"/><text x="45" y="47" text-anchor="middle" fill="#263e38" stroke="none" font-family="Arial" font-size="42">?</text>',
 chart:'<rect width="95" height="70" rx="8" fill="#f7e6ba"/><path d="M18 51l20-18 16 10 24-26" fill="none" stroke="#b2924e"/>',
 clock:'<circle cx="38" cy="38" r="34" fill="white"/><path d="M38 15v23l19 10" fill="none"/>',
 book:'<path d="M0 0q22-10 45 0q22-10 45 0v61q-22-10-45 0q-23-10-45 0Z" fill="#fff7df"/><path d="M45 0v61"/>',
 plant:'<path d="M22 55L10 82h53L52 55Z" fill="#c98048"/><path d="M36 59V8"/><path d="M36 35Q0 39 6 10Q33 7 36 35M36 23Q72 29 69 0Q40 0 36 23" fill="#8ba35d"/>',
 lightbulb:'<path d="M24 53Q-10 24 12 7Q38-12 60 7Q82 24 48 53v17H24Z" fill="#f4cb69"/><path d="M24 80h24M36-10v-9M-8 23h-9M80 23h9"/>',
 envelope:'<rect width="90" height="61" rx="7" fill="white"/><path d="M0 4l45 31L90 4" fill="none"/>',
 puzzle:'<path d="M0 0h25q-9-24 11-24q20 0 11 24h25v25q24-9 24 11q0 20-24 11v25H47q9-24-11-24q-20 0-11 24H0Z" fill="#edb955"/>',
 coffee:'<path d="M0 18h55v35Q28 75 0 53Z" fill="white"/><path d="M55 25h15q16 19-15 23M14 0q-10-10 0-20M35 0q-10-10 0-20" fill="none"/>',
 bridge:'<path d="M0 50Q55-30 110 50M0 50h110M15 35v30M35 13v52M55 5v60M75 13v52M95 35v30" fill="none" stroke="#799557"/>',
 balance:'<path d="M55 0v85M20 85h70M8 22h94M20 22L0 60h40ZM90 22L70 60h40Z" fill="#e5c276"/>',
 fork:'<path d="M50 85V45L10 0M50 45L90 0" fill="none" stroke="#c98048" stroke-width="12"/>',
 mountain:'<path d="M0 75L48 0l50 75Z" fill="#91b3b8"/><path d="M29 30L48 0l21 30-21-8Z" fill="white"/>',
 umbrella:'<path d="M0 40Q50-35 100 40Z" fill="#6e9bad"/><path d="M50 40v48q0 22-18 10" fill="none"/>',
 clipboard:'<rect width="67" height="90" rx="7" fill="white"/><rect x="19" y="-5" width="30" height="13" rx="4" fill="#cba97f"/><path d="M14 32h40M14 51h40M14 70h25"/>',
 arrow:'<path d="M0 25h90M70 5l20 20-20 20" fill="none" stroke="#799557"/>',
 stars:'<path d="M35 0l9 18 21 3-15 15 3 21-18-10-18 10 3-21L5 21l21-3Z" fill="#e9b94e"/>',
 ladder:'<path d="M10 0v100M65 0v100M10 20h55M10 45h55M10 70h55M10 95h55" fill="none"/>',
 bench:'<path d="M0 0h110v37H0ZM10 44h90M15 44v32M95 44v32" fill="#cba97f"/>',
 phone:'<rect width="45" height="75" rx="8" fill="#e5eff2"/><path d="M13 10h19M19 63h7"/>',
 speech:'<path d="M0 0h95v55H30L10 73V55H0Z" fill="white"/><path d="M17 18h60M17 35h38"/>',
 road:'<path d="M0 60Q45 5 95 50T170 20" fill="none" stroke="#dbc79f" stroke-width="18"/>',
 rain:'<path d="M0 0l-8 18M28 0l-8 18M56 0l-8 18" fill="none" stroke="#6e9bad"/>'
};
function character(c){
 const arm={up:'M-36 70L-67 38L-75 10M36 70L65 35L75 8',reach:'M-35 72L-54 108M36 70L81 87L106 81',cross:'M-37 74L-17 106L34 84M37 73L16 107L-31 86',think:'M-36 73L-40 110M36 73L59 37L24 29',point:'M-36 73L-52 117M36 73L85 43',down:'M-36 73L-52 117M36 73L52 117'}[c.pose];
 const brow={happy:'M-23-2Q-17-9-11-2M11-2Q17-9 23-2',skeptical:'M-24-1L-11 3M12-4L26-9',worried:'M-23-6l13-4M12-10l13 4',calm:'M-24 1h13M12 1h13',neutral:'M-22-3h12M12-3h12',curious:'M-24-7h13M12-12l13-4',determined:'M-23-8l13 5M12-3l13-5'}[c.face];
 const mouth=c.face==='happy'?'M-15 23Q0 42 16 23Z':c.face==='worried'?'M-14 31Q0 16 14 31':c.face==='skeptical'?'M-12 30L13 24':'M-13 27Q0 32 13 27';
 return `<g transform="translate(${c.x} ${c.y}) scale(${c.flip?-c.scale:c.scale} ${c.scale})" stroke="${ink}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"><path d="M-23 124L-28 181M23 124L28 181" fill="none"/><path d="M-44 77Q-40 52 0 52Q40 52 44 77L34 132H-34Z" fill="${c.shirt}"/><path d="${arm}" fill="none"/><circle cy="13" r="42" fill="#f3bf92"/><path d="M-41 4Q-46-30-15-35Q21-44 41-9L29-10L14-25Q-12-5-41 4" fill="#594634"/><path d="${brow}" fill="none"/><path d="${mouth}" fill="${c.face==='happy'?'white':'none'}" stroke-width="4"/></g>`;
}
function svg(scene){
 if(!scene||!/^#[a-fA-F0-9]{6}$/.test(scene.background)||!Array.isArray(scene.characters)||scene.characters.length>3||!scene.characters.length||!Array.isArray(scene.props)||scene.props.length>5)throw Error('Invalid scene');
 for(const c of scene.characters){if(!['happy','skeptical','worried','calm','neutral','curious','determined'].includes(c.face)||!['up','reach','cross','think','point','down'].includes(c.pose)||!/^#[a-fA-F0-9]{6}$/.test(c.shirt)||!Number.isFinite(c.x)||c.x<75||c.x>565||!Number.isFinite(c.y)||c.y<65||c.y>160||![0.85,1,1.15].includes(c.scale)||typeof c.flip!=='boolean')throw Error('Invalid character');}
 for(const p of scene.props){if(!Object.hasOwn(props,p.kind)||!Number.isFinite(p.x)||p.x<10||p.x>500||!Number.isFinite(p.y)||p.y<25||p.y>300||![0.7,1,1.2].includes(p.scale))throw Error('Invalid prop');}
 return `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="330" role="img"><title>${esc(scene.description)}</title><rect width="640" height="330" fill="${scene.background}"/><ellipse cx="320" cy="304" rx="245" ry="12" fill="#263e38" opacity=".08"/>${scene.props.map(p=>`<g transform="translate(${p.x} ${p.y}) scale(${p.scale})" stroke="${ink}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">${props[p.kind]}</g>`).join('')}${scene.characters.map(character).join('')}</svg>`;
}
async function renderEdition(root,edition){for(const l of edition.lessons){if(l.image==='essay'&&!l.illustration)continue;const target=path.join(root,l.illustration);if(!target.startsWith(path.join(root,'assets/english',edition.date)+path.sep))throw Error('Invalid illustration path');if(fs.existsSync(target))continue;fs.mkdirSync(path.dirname(target),{recursive:true});await sharp(Buffer.from(svg(l.scene))).png({palette:true,colours:128}).toFile(target);}}
module.exports={svg,renderEdition};
if(require.main===module){const root=path.resolve(__dirname,'..'),date=process.argv[2];const edition=JSON.parse(fs.readFileSync(path.join(root,'data/english-staged',date+'.json')));renderEdition(root,edition).catch(()=>{console.error('Comic rendering failed; the published edition is unchanged.');process.exit(1)});}
