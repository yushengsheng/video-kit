import {access, mkdir, readFile, rename, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const content=path.join(root,'content/handdraw-goji-inkred-v1');
const output=path.join(root,'out/handdraw-goji-inkred-v1');
const timeline=JSON.parse(await readFile(path.join(content,'timeline.json'),'utf8'));
const story=JSON.parse(await readFile(path.join(content,'story.json'),'utf8'));
const art=JSON.parse(await readFile(path.join(content,'art.json'),'utf8'));
const record=JSON.parse(await readFile(path.join(content,'narration-record.json'),'utf8'));
const sha=async p=>createHash('sha256').update(await readFile(path.join(root,p))).digest('hex');
if((!process.argv.includes('--stills')&&story.scenes.map(s=>s.id).join('|')!==art.map(s=>s.id).join('|'))||story.scenes.map(s=>s.id).join('|')!==timeline.scenes.map(s=>s.id).join('|'))throw Error('Scene IDs do not match');
if(story.scenes.flatMap(s=>s.captions).join('')!==record.text||record.text!==timeline.captions.map(c=>c.text).join('')||record.signature!==timeline.scriptSignature)throw Error('Narration and captions do not match');
if(['name','rate','pitch'].some(k=>story.voice[k]!==record.voice[k]))throw Error('Voice setting mismatch');
if(await sha('public/'+timeline.audio)!==timeline.audioSha256)throw Error('Narration hash mismatch');
let lastEnd=0;
for(const c of timeline.captions){if(c.startFrame<lastEnd||c.endFrame<=c.startFrame||c.endFrame>timeline.durationInFrames)throw Error('Caption timing invalid');lastEnd=c.endFrame;}
const sources=['content/handdraw-goji-inkred-v1/story.json','content/handdraw-goji-inkred-v1/art.json','content/handdraw-goji-inkred-v1/timeline.json','content/handdraw-goji-inkred-v1/narration-record.json','public/'+timeline.audio,'public/handdraw-goji-inkred-v1/audio/foley.wav','public/handdraw-goji-inkred-v1/paper.jpg','public/handdraw-goji-inkred-v1/fonts/MaShanZheng-Regular.ttf','public/fonts/NotoSerifSC-Regular.ttf','src/handdraw-goji-inkred-v1/Video.tsx','src/handdraw-goji-inkred-v1/index.tsx','scripts/render-goji-inkred.mjs','scripts/create_goji_inkred_art.py','scripts/create_goji_art.py','scripts/create_moon_art.py','scripts/create_moon_voice.py'];
const hashes=Object.fromEntries(await Promise.all(sources.map(async s=>[s,await sha(s)])));
await mkdir(output,{recursive:true});
const browserExecutable=process.env.REMOTION_BROWSER_EXECUTABLE||'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser';await access(browserExecutable);
const options={chromeMode:'chrome-for-testing',browserExecutable};
const serveUrl=await bundle({entryPoint:path.join(root,'src/handdraw-goji-inkred-v1/index.tsx'),publicDir:path.join(root,'public')});
const browser=await openBrowser('chrome',options);
try{
  const composition=await selectComposition({serveUrl,id:story.id,puppeteerInstance:browser,...options});
  if(process.argv.includes('--stills')){
    const requested=process.argv.find(a=>a.startsWith('--scenes='));
    const indices=requested?requested.split('=')[1].split(',').map(Number):timeline.scenes.map((_,i)=>i);
    for(const index of indices){
      const s=timeline.scenes[index];
      for(const local of process.argv.includes('--phases')?[.7,art[index].paintAt+.5,Math.min(s.durationInFrames/30-.2,5.0)]:[Math.min(s.durationInFrames/30-.2,5.0)]){
        const frame=s.from+Math.round(local*30);
        await renderStill({serveUrl,composition,frame,output:path.join(output,`scene-${String(index+1).padStart(2,'0')}-${local.toFixed(2)}.png`),scale:.5,imageFormat:'png',puppeteerInstance:browser,...options});
        console.log(`Still ${s.id} ${local}`);
      }
    }
  }else{
    const preview=process.argv.includes('--preview');
    const frames=preview?timeline.scenes[0].durationInFrames:timeline.durationInFrames;
    const name=preview?'给生活添一抹红-720p短预览-v1.mp4':'给生活添一抹红-手绘短片-v1.mp4';
    const temporary=path.join(output,preview?'preview-rendering.mp4':'full-rendering.mp4');
    let last=-1;
    await renderMedia({serveUrl,composition,outputLocation:temporary,frameRange:[0,frames-1],scale:preview?2/3:1,codec:'h264',audioCodec:'aac',pixelFormat:'yuv420p',colorSpace:'bt709',imageFormat:'png',crf:18,concurrency:2,puppeteerInstance:browser,...options,
      onProgress:({progress})=>{const p=Math.floor(progress*20)*5;if(p!==last){console.log(`渲染 ${p}%`);last=p;}}});
    const film=path.join(output,name);await rename(temporary,film);
    const filmHash=createHash('sha256').update(await readFile(film)).digest('hex');
    await writeFile(path.join(output,preview?'preview-render.json':'render.json'),JSON.stringify({film,film_sha256:filmHash,frames,dimensions:preview?[1280,720]:[1920,1080],fps:30,input_hashes:hashes},null,2));
    console.log(film);
  }
}finally{await browser.close({silent:true});}
