import {access, mkdir, readFile, rename} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {bundle} from '@remotion/bundler';
import {openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const story = JSON.parse(await readFile(path.join(root, 'content/handdraw-moon-v1/story.json'), 'utf8'));
const timeline = JSON.parse(await readFile(path.join(root, 'content/handdraw-moon-v1/timeline.json'), 'utf8'));
const narration = JSON.parse(await readFile(path.join(root, 'content/handdraw-moon-v1/narration-record.json'), 'utf8'));
const outputDir = path.join(root, 'out/handdraw-moon-v1');
await mkdir(outputDir, {recursive: true});
for (const resource of ['fonts/NotoSerifSC-Regular.ttf', 'handdraw-moon-v1/paper.jpg', 'handdraw-moon-v1/drawing-hand.png', timeline.audio]) {
  await access(path.join(root, 'public', resource));
}
let previousEnd = 0;
for (const caption of timeline.captions) {
  if (!caption.text || caption.startFrame < previousEnd || caption.endFrame <= caption.startFrame || caption.endFrame > timeline.durationInFrames) throw new Error('字幕时间轴无效');
  previousEnd = caption.endFrame;
}
if (story.scenes.map(s => s.id).join('|') !== timeline.scenes.map(s => s.id).join('|')) throw new Error('分镜与旁白顺序不符');
if (story.scenes.flatMap(s=>s.captions).join('') !== narration.text || timeline.scriptSignature !== narration.signature
  || ['name','rate','pitch'].some(key=>story.voice[key] !== narration.voice[key])) throw new Error('旁白记录与当前文案或音色不符');
if (createHash('sha256').update(await readFile(path.join(root,'public',timeline.audio))).digest('hex') !== timeline.audioSha256) throw new Error('音频已改变，需要重新生成时间轴');
const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE || '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser';
await access(browserExecutable);
const options = {chromeMode:'chrome-for-testing', browserExecutable};
const serveUrl = await bundle({entryPoint:path.join(root,'src/handdraw-moon/index.tsx'),publicDir:path.join(root,'public')});
const browser = await openBrowser('chrome',options);
const onBrowserLog = log => {if (log.type === 'error') console.error(log.text);};
try {
  const composition = await selectComposition({serveUrl,id:story.id,...options,puppeteerInstance:browser,onBrowserLog});
  if (process.argv.includes('--stills')) {
    for (const [index, scene] of timeline.scenes.entries()) {
      for (const progress of process.argv.includes('--all-phases') ? [.28,.72,.96] : [.96]) {
        const frame = scene.from+Math.min(scene.durationInFrames-2,Math.floor(scene.durationInFrames*progress));
        await renderStill({serveUrl,composition,frame,output:path.join(outputDir,`scene-${index+1}-${progress}.png`),imageFormat:'png',scale:.5,...options,puppeteerInstance:browser,onBrowserLog});
        console.log(`检查 ${scene.id} ${progress}`);
      }
    }
  } else {
    const preview = process.argv.includes('--preview');
    const temporary = path.join(outputDir,preview?'preview-rendering.mp4':'film-rendering.mp4');
    const final = path.join(outputDir,preview?'井里的月亮-短预览-v1.mp4':'井里的月亮-手绘故事-v1.mp4');
    let last = -1;
    await renderMedia({serveUrl,composition,outputLocation:temporary,codec:'h264',audioCodec:'aac',crf:18,pixelFormat:'yuv420p',imageFormat:'png',colorSpace:'bt709',concurrency:2,
      ...(preview ? {frameRange:[0,Math.min(timeline.durationInFrames-1,timeline.scenes[1].from-1)],scale:2/3} : {}),
      ...options,puppeteerInstance:browser,onBrowserLog,onProgress:({progress})=>{const p=Math.floor(progress*20)*5;if(p!==last){console.log(`渲染 ${p}%`);last=p;}}
    });
    await rename(temporary,final);
    console.log(final);
  }
} finally {
  await browser.close({silent:true});
}
