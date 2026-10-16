import {browserExecutable as findBrowser} from './browser.mjs';
import {access, mkdir, readFile, rename, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [jobArgument, mode, resolution] = process.argv.slice(2);
if (!['preview','full'].includes(mode) || !['720p','1080p'].includes(resolution)) throw new Error('未知渲染模式或尺寸');
const inside = (filename, directory) => {const p=path.resolve(filename);if(!p.startsWith(path.resolve(directory)+path.sep))throw new Error('任务路径越界');return p;};
const jobPath = inside(jobArgument,path.join(root,'public/comfyui-handdraw'));
const jobDir = path.dirname(jobPath);
const job = JSON.parse(await readFile(jobPath,'utf8'));
const sha = async filename=>createHash('sha256').update(await readFile(filename)).digest('hex');
for (const [file,hash] of Object.entries(job.input_hashes)) if(await sha(inside(path.join(jobDir,file),jobDir))!==hash)throw new Error(`素材改变：${file}`);
for (const [file,hash] of Object.entries(job.engine_files)) if(await sha(inside(path.join(root,file),root))!==hash)throw new Error('渲染代码已更新，请重新准备任务');
const story = JSON.parse(await readFile(path.join(jobDir,'story.json'),'utf8'));
const timing = JSON.parse(await readFile(path.join(jobDir,'timeline.json'),'utf8'));
const art = JSON.parse(await readFile(path.join(jobDir,'art.json'),'utf8'));
const inputProps = {title:story.title,timing,art,assets:job.assets};
const directory = path.join(root,'out/comfyui-handdraw',job.fingerprint.slice(0,20),`${mode}-${resolution}`);
await mkdir(directory,{recursive:true});
const final = path.join(directory,'film.mp4');
const recordPath = path.join(directory,'render.json');
let cached;
try {cached=JSON.parse(await readFile(recordPath,'utf8'));} catch(error) {if(error.code!=='ENOENT')throw error;}
if (cached && await sha(final)===cached.film_sha256) {console.log(JSON.stringify({render:recordPath,cached:true}));process.exit(0);}
const browserExecutable=findBrowser();
await access(browserExecutable);
const options={chromeMode:'chrome-for-testing',browserExecutable};
const serveUrl=await bundle({entryPoint:path.join(root,'src/handdraw-moon/comfy.tsx'),publicDir:path.join(root,'public')});
const browser=await openBrowser('chrome',options);
const scale=resolution==='720p'?2/3:1;
const frames=mode==='preview'?timing.scenes[0].durationInFrames:timing.durationInFrames;
try {
  const composition=await selectComposition({serveUrl,id:'HanddrawWorkflow',inputProps,...options,puppeteerInstance:browser});
  const temporary=path.join(directory,'rendering.mp4');
  let last=-1;
  await renderMedia({serveUrl,composition,inputProps,outputLocation:temporary,codec:'h264',audioCodec:'aac',crf:18,pixelFormat:'yuv420p',imageFormat:'png',colorSpace:'bt709',concurrency:2,scale,frameRange:[0,frames-1],
    ...options,puppeteerInstance:browser,onProgress:({progress})=>{const p=Math.floor(progress*20)*5;if(p!==last){console.log(`渲染 ${p}%`);last=p;}}});
  await rename(temporary,final);
  const posterFrame=Math.min(frames-1,Math.round(timing.scenes[0].durationInFrames*.94));
  await renderStill({serveUrl,composition,inputProps,frame:posterFrame,output:path.join(directory,'cover.png'),imageFormat:'png',scale,...options,puppeteerInstance:browser});
  const record={job:jobPath,film:final,film_sha256:await sha(final),mode,resolution,frames,dimensions:[Math.round(1920*scale),Math.round(1080*scale)],renderer:'Remotion / Brave',duration_seconds:frames/30};
  await writeFile(recordPath,JSON.stringify(record,null,2));
  console.log(JSON.stringify({render:recordPath,cached:false}));
} finally {await browser.close({silent:true});}
